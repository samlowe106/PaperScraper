from .submission_wrapper import SubmissionWrapper
from . import sign_in

source_dict = {
    "top" : lambda sub, age, score: sub.top(age_limit=age, score_limit=score),
    "new" : lambda sub, age, score: sub.new(age_limit=age, score_limit=score),
    "hot" : lambda sub, age, score: sub.hot(age_limit=age, score_limit=score),
    "controversial" : lambda sub, age, score: sub.controversial(age_limit=age, score_limit=score),
    "gilded" : lambda sub, age, score: sub.gilded(age_limit=age, score_limit=score),
}

SORT_OPTIONS = source_dict.keys()

source_dict["identity"] = lambda saved, _, __: saved

class SubmissionSource:
    """
    Represents a source of reddit posts, such as a subreddit or user's saved posts
    """

    count = 0

    def __init__(self, args, view):
        self.score_minimum = args.score
        self.limit = args.limit

        if args.source == "saved":
            if args.sortby is not None:
                raise ValueError(f"No way to sort saved posts by {args.sortby}")
            while not (args.username and args.password):
                view.prompt_sign_in()
            reddit = sign_in(args.username, args.password)
            self.original_source = reddit.user.me().saved()

        elif args.source.startswith("r/"):
            # raises prawcore.NotFound ??
            self.original_source = source_dict[args.sortby](
                reddit.subreddit(args.source.rstrip("/r")),
                args.age,
                args.score)
        else:
            raise ValueError(f"Expected source to be saved or a subreddit, got {args.source}")


    def __iter__(self):
        for submission in self.original_source:
            wrapper = SubmissionWrapper(submission)
            if (self.count < self.limit
                and wrapper.score_at_least(self.score_minimum)
                and wrapper.posted_after()
                and wrapper.count_parsed() > 0):
                self.count += 1
                yield SubmissionWrapper(submission)
