from flask import jsonify, render_template, redirect, request, url_for, flash
from app import app, celery, redis, db
from models import Account, Service
import bi.commands as commands
import bi.helpers as helpers
import settings


@app.route('/')
def index():
    successful = helpers.get_dict_from_list('successful', 20)
    failed = helpers.get_dict_from_list('failed', 20)
    accs = Account.query.count()
    servs = Service.query.count()

    for a in successful:
        item = Account.query.get(a['account_id'])
        if item is None:
            a['alive'] = False
        else:
            a['alive'] = True

    for a in failed:
        item = Account.query.get(a['account_id'])
        if item is None:
            a['alive'] = False
        else:
            a['alive'] = True

    return render_template('index.html', finished=successful, failed=failed,
            accs=accs, servs=servs)


@app.route('/running')
def get_running():
    running = helpers.get_dict_from_list('running')
    return render_template('running.html', count=len(running), running=running)


@app.route('/queued')
def get_queued():
    i = celery.control.inspect()
    active = i.reserved()
    return jsonify({'running': active})


@app.route('/log/<id>')
def logs(id):
    log = redis.get('%s_l' % id)
    if log is None:
        return "Nothing found"

    info = redis.hgetall(id)
    logs = log.split('\n')
    return render_template('logs.html', logs=logs, info=info,
            log_id=id)


@app.route('/logdata/<id>')
def logdata(id):
    log = redis.get('%s_l' % id)
    logs = log.split('\n')
    return jsonify({'logs': logs})


@app.route('/new/<type>/user')
def new_user(type):
    id = commands.new_user(type)
    flash("Creating New User | Job %s" % id, 'success')
    return redirect(request.referrer)


@app.route('/upvote/<type>')
def upvote(type):
    id = commands.custom_action('upvote', type, {})
    flash("Going up! | Job %s" % id, 'success')
    return redirect(request.referrer)


@app.route('/account/<id>')
def get_account(id):
    account = Account.query.get(id)
    if account is None:
        flash("No user exists for that ID", 'warning')
        return redirect(request.referrer)

    return render_template('account.html', account=account)


@app.route('/account/<id>/delete')
def delete_account(id):
    account = Account.query.get(id)

    if account is not None:
        db.session.delete(account)
        db.session.commit()
        flash('%s deleted' % account.username, 'success')
    else:
        flash("No user found", 'warning')

    return redirect(url_for('index'))


@app.route('/action', methods=['GET', 'POST'])
def custom_action():
    opt_count = 5
    if request.method == 'GET':
        services = db.session.query(Service.id, Service.type).all()
        return render_template('custom.html', services=services, opt_count=opt_count)

    elif request.method == 'POST':
        print request.form
        service = Service.query.get(request.form['service'])
        if service is None:
            return

        action = request.form['action']
        if action is None:
            return

        options = {}
        for i in xrange(0, opt_count):
            opt = request.form['opt%s' % i]
            if opt is not None:
                value = request.form['opt%s-val' % i]
                options[opt] = value

        count = int(request.form['count'])

        if count == 1:
            job_id = commands.custom_action(action, service, options)
            flash("Performing %s | Job ID: %s" % (action, job_id), 'success')

        else:
            for i in xrange(0, count):
                commands.custom_action(action, service, options)
            flash("Performing %s %s operataions" % (count, action), 'success')

        return redirect(url_for('get_running'))


@app.route('/go/<place>')
def go(place):
    if place == 'captcha':
        return redirect('http://%s:%s' % (settings.CAPTCHA_HOST, settings.CAPTCHA_PORT))

    if place == 'flower':
        return redirect('http://%s:%s' % (settings.FLOWER_HOST, settings.FLOWER_PORT))

    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host=settings.HOST)
