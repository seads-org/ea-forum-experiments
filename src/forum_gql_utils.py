import requests
from tqdm.auto import trange

EA_GQL_URL = 'https://forum.effectivealtruism.org/graphql'
USER_QUERY = """
{{
  users(input: {{
    {terms}
  }}) {{
    results {{
      _id
      username
      karma
      bio
      pageUrl
      createdAt
      deleted
      banned
      profileTags {{
        name
      }}
      posts {{
        _id
      }}
      commentCount
    }}
  }}
}}
"""

POST_QUERY = """
{{
  posts(input: {{
    {terms}
  }}) {{
    results {{
      _id
      title
      htmlBody
      pageUrl
      postedAt
      baseScore
      voteCount
      commentCount
      meta
      question
      url
      tags {{
        name
      }}
      user {{
        username
        _id
      }}
      coauthors {{
        username
        _id
      }}
    }}
  }}
}}
"""

COMMENTS_QUERY = """
{{
  comments(input: {{
    {terms}
  }}) {{
    results {{
      _id
      postId
      pageUrl
      user {{
        username
        _id
      }}
      voteCount
      htmlBody
      spam
      deleted
      retracted
      allVotes {{
        voteType
      }}
      score
      baseScore
    }}
  }}
}}
"""

def getQuery(limit, offset, content):
    terms = f"""
        terms: {{
            limit: {limit},
            offset: {offset}
        }}
    """

    if content == "users":
        query = USER_QUERY.format(terms=terms)
    elif content == "posts":
        query = POST_QUERY.format(terms=terms)
    elif content == "comments":
        query = COMMENTS_QUERY.format(terms=terms)
    else:
        raise ValueError("content must be either 'users', 'comments' or 'posts'")

    return query


def scrape_forum(url:str, content:str, limit:int, step:int = 5000):
    objects = []
    for si in trange(0, limit, step):
        res = requests.post(url, json={'query': getQuery(limit=step, offset=si, content=content)})
        try:
            objects.extend(res.json()['data'][content]['results'])
        except Exception as e:
            print(e)
            return res

    return objects