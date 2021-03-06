from app import settings, db
from models import Service, Account
from bi import runner


def new_user(type, custom_options={}):
    service = Service.query.filter(Service.type == type).one()
    account = Account()
    account.fill(service)
    db.session.add(account)
    db.session.commit()

    return custom_action('new_user', service, custom_options, account=account)


def custom_action(action, service, custom_options, account=None):
    if isinstance(service, str):
        # Assume its a service type
        service = Service.query.filter(Service.type == type).one()

    if not account:
        account = get_account(service)

    # if still no account
    if not account:
        return

    options = {
        'username': account.username,
        'password': account.password
    }

    options = add_service_options(options, service)

    for key, value in custom_options.iteritems():
        options[key] = value

    command = get_command(account, action, options)
    info = get_info(options, action, account, service)

    account.active = True
    db.session.add(account)
    db.session.commit()

    job = runner.run_command.delay(str(command), info)
    return job.id


def get_account(service):
    account = Account.query.filter(Account.service_id == service.id). \
            filter(Account.active == False). \
            order_by(Account.last_action).first()

    return account


def get_command(account, action, options={}):
    action += '.js'
    path = "casperjs %s/adapters/%s/%s" % (settings.PATH, account.service.type, action)

    for key, value in options.iteritems():
        path += ' --%s="%s"' % (key, value)

    try:
        for key, value in settings.OPTIONS.iteritems():
            path += ' --%s="%s"' % (key, value)
    except AttributeError:
        pass

    return path


def add_service_options(options, service):
    for key, value in service.options.iteritems():
        options[key] = value

    return options


def get_info(options, action, account, service):
    options['action'] = action
    options['account_id'] = account.id
    options['service'] = service.type
    return options
