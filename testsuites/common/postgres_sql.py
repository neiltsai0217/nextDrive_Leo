from libs.database_utils import postgres_query_all, postgres_query_one


def get_gateway(pid):
    sql = """
        select * from eg3.public.gateways where pid = %(pid)s
    """

    return postgres_query_one(sql, pid=pid)


def get_devices(pid):
    sql = """
        select * from eg3.public.devices
            where gateway_id in (
                select g.id from eg3.public.gateways g where pid = %(pid)s
        )
    """
    return postgres_query_all(sql, pid=pid)


def get_event_subscriptions(limit=501):
    sql = """
        select *
            from ioe_event_dispatch.event_subscriptions limit %(limit)s
    """
    return postgres_query_all(sql, limit=limit, dbname='ioe_event_dispatch')