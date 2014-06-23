import json

from rbtools.api.client import RBClient
from rbtools.api.errors import APIError


def post_reviews(url, username, password, repo, identifier, commits):
    """Post a set of commits to Review Board.

    Repository hooks can use this function to post a set of pushed commits
    to Review Board. Each commit will become its own review request.
    Additionally, a review request with a diff encompassing all the commits
    will be created; This "squashed" review request will represent the push
    for the provided `identifier`.

    The `identifier` is a unique string which represents a series of pushed
    commit sets. This identifier is used to update review requests with a new
    set of diffs from a new push. Generally this identifier will represent
    some unit of work, such as a bug.

    The `commits` argument ... TODO: Define the commits argument.

        {

        }
    """
    rbc = RBClient(url, username=username, password=password)

    try:
        api_root = rbc.get_root()
    except APIError as ex:
        return (1, "ERROR: Could not contact the Review Board server - %s" % ex)


    # Retrieve the squashed review request or create it.
    previous_commits = []
    squashed_rr = None
    rrs = api_root.get_review_requests(commit_id=identifier,
                                       repository=repo)

    if rrs.total_results > 0:
        squashed_rr = rrs[0]
    else:
        # A review request for that identifier doesn't exist - this
        # is the first push to this identifier and we'll need to create
        # it from scratch.
        data = {
            "extra_data.p2rb": "True",
            "extra_data.p2rb.is_squashed": "True",
            "extra_data.p2rb.identifier": identifier,
            "commit_id": identifier,
            "repository": repo,
        }
        squashed_rr = rrs.create(data=data)

    squashed_rr.get_diffs().upload_diff(commits["squashed"]["diff"])

    previous_commits = get_previous_commits(squashed_rr)


    # Create/update the individual commit review requests. Currently
    # we will update them in push order, with no thought to history
    # rewrites which reordered, squashed, or deleted commits.
    #
    # TODO: Handle rebasing using information provided to us. This
    # most likely requires some sort of extra UI or calculations
    # on the callers part, along with more intelligence when updating
    # the review requests
    reviewmap = {}
    draft_rrs = []
    commits_list = []
    new_commits = []
    individuals = commits['individual']
    np = len(previous_commits)
    ni = len(individuals)
    i = 0

    for i in range(max(np, ni)):
        pcid, rid = previous_commits[i] if i < np else (None, None)
        commit = individuals[i] if i < ni else None
        rr = None

        if pcid is not None and commit is not None:
            # We have a previous commit and a new commit to
            # update it with.
            rr = update_or_create_commit_rr(api_root, commit, rid=rid,
                                            pcid=pcid)

        elif pcid is not None and commit is None:
            # We have a previous commit but no new commit. We need
            # to discard this now-unused review request.
            pass
        else:
            # There is no previous commit so we need to create one
            # from scratch.
            data = {
                "extra_data.p2rb": "True",
                "extra_data.p2rb.is_squashed": "False",
                "extra_data.p2rb.identifier": identifier,
                "commit_id": commit["id"],
                "repository": repo,
            }

            rr = rrs.create(data=data)
            rr.get_diffs().upload_diff(commit["diff"],
                                       parent_diff=commit["parent_diff"])

            draft = rr.get_or_create_draft(**{
                "summary": commit['message'].rsplit("\n", 1)[0],
                "description": commit['message']
            })


        if commit is not None:
            reviewmap[commit['id']] = rr.id
            commits_list.append((commit['id'], rr.id))
            draft_rrs.append(draft)


    squashed_description = []
    for rr in draft_rrs:
        squashed_description.append(
            "/r/%s - %s" % (rr.id, rr.summary))


    squashed_draft = squashed_rr.get_or_create_draft(**{
        "summary": "Review for review ID: %s" % identifier,
        "description": "\n".join(squashed_description),
        "depends_on": ",".join([str(rr.id) for rr in draft_rrs]),
        "extra_data.p2rb.commits": json.dumps([
            (draft.commit_id, draft.id) for draft in draft_rrs
        ]),
    })

    return squashed_rr.id, reviewmap


def get_previous_commits(squashed_rr):
    """Retrieve the previous commits from a squashed review request.

    This will return a list of tuples specifying the previous commit
    id as well as the review request it is represented by. ex::
        [
            # (<commit-id>, <review-request-id>),
            ('d4bd89322f54', '13'),
            ('373537353134', '14'),
        ]
    """
    extra_data = squashed_rr.extra_data
    commits = (
        extra_data["p2rb.commits"] if "p2rb.commits" in extra_data else "[]")
    print commits
    return json.loads(commits)

























#




