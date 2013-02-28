from app import redis


def get_dict_from_list(name, count=-1):
    items = redis.lrange(name, 0, count)
    ret = []
    for id in items:
        item = redis.hgetall(id)
        item['job_id'] = id
        ret.append(item)

    return ret
