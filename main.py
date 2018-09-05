"""
A flask API that acts as a middleman,
between the user and the mounts class
:contributors
- Daniel Quackenbush
"""
import logging
from json import dumps, loads
from flask import Flask, request, Response
from flask_restful import Resource
from mounts import Mounts, ExistsException


app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


def error(message, code=400):
    """
    :input message - to error with
    :input code - optional error code
    :return code Response Object
    """
    app.logger.info(f"{code}: {request.method} - {request.url}")
    body = {'message': str(message)}
    return Response(dumps(body), status=code, mimetype='application/json')


def ok(body):
    """
    :input body - json to respond with
    :return 200 Response Object
    """
    app.logger.info(f"200: {request.method} - {request.url}")
    return Response(dumps(body), status=200, mimetype='application/json')


def not_found():
    """
    :return 404 Response Object
    """
    app.logger.info(f"404: {request.method} - {request.url}")
    return Response('', status=404, mimetype='application/json')


@app.route('/', methods=['GET'])
def health_index():
    """
    A simple health status to know the app is running
    """
    return ok({'message': 'active'})


@app.route('/mounts', methods=['GET'])
def mounts_index():
    """
    A readness test will ensure you have the most up to date pull
    returns all mounts
    TODO: Place an index to avoid large returns
    """
    return ok(Mounts(app=app).nfs_info)


@app.route('/mounts/<string:host_type>', methods=['GET', 'POST', 'PUT'])
def mounts_host_type_index(host_type):
    """
    The host type index (hosts/hostgroups) - Allows you to get, put, or post host_type info
    ex. GET /mounts/hosts - returns all hosts
    """
    if request.method == 'GET':
        try:
            return ok(Mounts(app=app).nfs_info[f"nfs_mounts::{host_type}"])
        except BaseException:
            return error('invalid type. must be hostgroups or hosts')
    elif request.method == 'POST' or request.method == 'PUT':
        data = {}
        try:
            data = loads(request.data)
        except BaseException:
            return error('invalid json body. Please check syntax')
        if 'options' not in data.keys():
            data['options'] = 'rw,bg,suid,soft,rsize=16384,wsize=16384,vers=3,tcp'
        if 'owner' not in data.keys():
            data['owner'] = 'root'
        if 'group' not in data.keys():
            data['group'] = 'root'
        if 'local_path' not in data.keys():
            return error('missing local_path for mount point')
        if 'share_path' not in data.keys():
            return error('missing share_path for NAS share')
        if 'name' not in data.keys():
            return error('missing name for host or hostgroup')

        if host_type == 'hosts':
            try:
                return ok(Mounts(app=app).add_nas_share(
                    host=data['name'],
                    local_path=data['local_path'],
                    share_path=data['share_path'],
                    owner=data['owner'],
                    group=data['group'],
                    options=data['options']
                ))
            except ExistsException as exc:
                return error(exc)
            except Exception as exc:
                return error(code=500, message=exc)
        elif host_type == 'hostgroups':
            try:
                return ok(Mounts(app=app).add_nas_share(
                    hostgroup=data['name'],
                    local_path=data['local_path'],
                    share_path=data['share_path'],
                    owner=data['owner'],
                    group=data['group'],
                    options=data['options']
                ))
            except ExistsException as exc:
                return error(exc)
            except Exception as exc:
                return error(code=500, message=exc)
        else:
            return error('invalid type. must be hostgroups or hosts')


@app.route(
    '/mounts/<string:host_type>/<string:name>',
    methods=[
        'GET',
        'DELETE'])
def host_index(host_type, name):
    """
    The host index - Allows you to get all mounts or delete all mounts from being managed
    ex. GET /mounts/hosts/hostname.example.com - returns all mounts for that host
    """
    if request.method == 'GET':
        try:
            return ok(
                Mounts(
                    app=app).nfs_info[f"nfs_mounts::{host_type}"][name])
        except KeyError:
            return not_found()
        except Exception as exc:
            return error(exc)
    else:
        try:
            Mounts(app=app).delete_host_name(host_type=host_type, name=name)
            return ok(f'successfully deleted {name}')
        except KeyError:
            return not_found()
        except Exception as exc:
            return error(exc)


@app.route(
    '/mounts/<string:host_type>/<string:name>/<string:uuid>',
    methods=[
        'GET',
        'DELETE',
        'PATCH'])
def host_mount_index(host_type, name, uuid):
    """
    The individual mount index - Allows get, delete, or patch (update a mount)
    ex. GET /mounts/hosts/hostname.example.com/<uuid> - returns a particular mount for that host
    """
    if request.method == 'GET':
        try:
            return ok([x for x in Mounts(
                app=app).nfs_info[f"nfs_mounts::{host_type}"][name] if x['uuid'] == uuid])
        except KeyError:
            return not_found()
        except Exception as exc:
            return error(exc)
    elif request.method == 'DELETE':
        try:
            Mounts(app=app).delete_host_mount(
                host_type=host_type,
                name=name,
                uuid_num=uuid)
            return ok(f'successfully deleted mount {uuid} for {name}')
        except KeyError:
            return not_found()
        except Exception as exc:
            return error(exc)
    else:
        data = {}
        try:
            data = loads(request.data)
        except BaseException:
            return error('invalid json body. Please check syntax')
        try:
            if host_type == 'hostgroups':
                return ok(Mounts(app=app).update_nas_share(
                    uuid_num=uuid,
                    replacement_dict=data,
                    hostgroup=name))
            elif host_type == 'hosts':
                return ok(Mounts(app=app).update_nas_share(
                    uuid_num=uuid,
                    replacement_dict=data,
                    host=name))
        except KeyError:
            return not_found()
        except Exception as exc:
            return error(exc)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
