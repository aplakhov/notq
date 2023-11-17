import random
import numpy as np
import heapq

vecs_dimension = 32

rnd = np.random.default_rng()
def smallRandomVec():
    return rnd.random(vecs_dimension) * 0.1 - 0.05

def getTimelessScore(userVec, postVec):
    return 1 / (1 + np.exp(-np.dot(userVec, postVec)))
    
def getProbableScore(userVec, post, timeSeconds):
    dot = np.dot(userVec, post["vec"])
    timediff = timeSeconds - post["created"]
    halflife = 480 * 3600
    decay = halflife / (halflife + timediff)
    return decay / (1 + np.exp(-dot))

class Recommender2:
    posts = []
    authorVecs = {}
    userVecs = {}

    def addPost(self, author, content, timeSeconds):
        if author not in self.authorVecs:
            self.authorVecs[author] = np.zeros(vecs_dimension)
        vec = np.copy(self.authorVecs[author])
        id = len(self.posts)
        post = { "author": author, "content": content, "created": timeSeconds, "vec": vec, "id": id, "upvotes": 0, "downvotes": 0 }
        self.posts.append(post)
        return id

    def getTopPostsFor(self, user, n, timeSeconds):
        if user not in self.userVecs:
            self.userVecs[user] = smallRandomVec()
        userVec = self.userVecs[user]
        return heapq.nlargest(n, self.posts, key=lambda post: getProbableScore(userVec, post, timeSeconds))

    def getNewUserVec(self):
        res = np.zeros(vecs_dimension)
        for _, vec in self.userVecs.items():
            res += vec
        res /= len(self.userVecs)
        return res

    def getTopPostsForNew(self, n, timeSeconds):
        userVec = self.getNewUserVec()
        return heapq.nlargest(n, self.posts, key=lambda post: getProbableScore(userVec, post, timeSeconds))

    def vote(self, user, post, score):
        predictedScore = getTimelessScore(self.userVecs[user], post["vec"])
        discrepancy = score - predictedScore
        alpha = 0.05
        delta = self.userVecs[user] * (alpha * discrepancy)
        self.userVecs[user] += post["vec"] * (alpha * discrepancy)
        post["vec"] += delta
        if score > 0:
            post["upvotes"] += 1
        elif score < 0:
            post["downvotes"] += 1
        #self.authorVecs[post["author"]] += delta * 0.1

def getRedditScore(post, timeSeconds):
    timediff = timeSeconds - post["created"]
    halflife = 18 * 3600
    decay = halflife / (halflife + timediff)
    return decay * (post["upvotes"] + 4 - post["downvotes"])

class Recommender:
    posts = []

    def addPost(self, author, content, timeSeconds):
        id = len(self.posts)
        post = { "author": author, "content": content, "created": timeSeconds, "id": id, "upvotes": 0, "downvotes": 0 }
        self.posts.append(post)
        return id

    def getTopPostsFor(self, user, n, timeSeconds):
        user #unused
        return self.getTopPostsForNew(n, timeSeconds)

    def getTopPostsForNew(self, n, timeSeconds):
        return heapq.nlargest(n, self.posts, key=lambda post: getRedditScore(post, timeSeconds))

    def vote(self, user, post, score):
        user # unused
        if score > 0:
            post["upvotes"] += 1
        elif score < 0:
            post["downvotes"] += 1

def firstTest():
    r = Recommender()
    # there are 5 authors with 2-3 posts every day
    # every author creates posts with normally distributed around x quality
    authors = [4, 3, 2, 1, -1]
    probPost = 2.5 / 13
    # there are 30 users with 2-3 visits every day
    users = ["user" + str(n) for n in range(30)]
    probVisit = 2.5 / 13
    # they do not vote twice
    alreadyVoted = {}
    # simulate everything for ndays
    ndays = 30
    for day in range(ndays):
        sumReadingQuality = 0
        numReads = 0
        for hour in range(10, 23):
            for a in authors:
                if random.random() < probPost:
                    quality = a + random.normalvariate(0, 2)
                    timestamp = day * 24 * 3600 + hour * 3600 + random.randint(0, 3600)
                    r.addPost("author" + str(a), quality, timestamp)
                    #print(f"author{a} added post with quality {quality} at day {day} hour {hour}")
            for user in users:
                if random.random() < probVisit:
                    timestamp = day * 24 * 3600 + hour * 3600 + random.randint(0, 3600)
                    posts = r.getTopPostsFor(user, 10, timestamp)
                    for post in posts:
                        # do not vote twice
                        key = str(post["id"]) + user
                        if not key in alreadyVoted:
                            alreadyVoted[key] = True
                            quality = post["content"]
                            userUpvoteThreshold = random.normalvariate(2, 1)
                            userDownvoteThreshold = random.normalvariate(-1, 1)
                            if quality > userUpvoteThreshold:
                                vote = 1
                            elif quality < userDownvoteThreshold:
                                vote = -1
                            else:
                                vote = 0
                            if vote:
                                r.vote(user, post, vote)
                            numReads += 1
                            sumReadingQuality += quality
                    if random.random() < 0.2:
                        break
        if numReads == 0:
            break
        print(f"Day {day}. Num posts {len(r.posts)}. Num reads {numReads}, avg reading quality {sumReadingQuality / numReads}")
    
    lastTimestamp = ndays * 24 * 3600
    posts = r.getTopPostsForNew(25, lastTimestamp)
    n = 0
    for post in posts:
        n += 1
        timediff = (lastTimestamp - post["created"]) / 24 / 3600
        print(f"{n}. {post['content']} of author {post['author']}")
        print(f"    created {timediff} days ago")
        print(f"    {post['upvotes']} up, {post['downvotes']} down")

firstTest()
