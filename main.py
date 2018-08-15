
import logging
from json import dumps, loads
from flask import Flask, request, Response
from flask_restful import Resource

from mounts import Mounts, ExistsException
from os import environ

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

def error(message, code=400):
    app.logger.info(f"{code}: {request.method} - {request.url_rule}")
    body = {'message': str(message)}
    return Response(dumps(body), status=code, mimetype='application/json')

def ok(body):
    app.logger.info(f"200: {request.method} - {request.url_rule}")
    return Response(dumps(body), status=200, mimetype='application/json')

def not_found():
    app.logger.info(f"404: {request.method} - {request.url_rule}")
    return Response('', status=404, mimetype='application/json')

@app.route('/', methods = ['GET'])
def health_index():
    return ok({'message': 'active' })

@app.route('/mounts', methods = ['GET'])
def mounts_index():
    return  ok(Mounts(app).nfs_info)

@app.route('/mounts/<string:host_type>', methods = ['GET', 'POST', 'PUT'])
def mounts_host_type_index(host_type):
    if request.method == 'GET':
        try:
            return ok(Mounts(app).nfs_info[host_type])
        except:
            return error('invalid type. must be hostgroups or hosts')
    elif request.method == 'POST' or request.method == 'PUT':
        data = {}
        try:
            data = loads(request.data)
        except:
            return error('invalid json body. Please check syntax')
        if 'options' not in data.keys():
            data['options'] = 'rw,suid,soft,rsize=16384,wsize=16384,vers=3,tcp'
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
                return ok(Mounts(app).add_nas_share(
                    host=data['name'],
                    local_path=data['local_path'],
                    share_path=data['share_path'],
                    owner = data['owner'],
                    group = data['group'],
                    options=data['options']
                ))
            except ExistsException as e:
                return error(e)
            except Exception as e:
                return error(code=500, message=e)
        elif host_type == 'hostgroups':
            try:
                return ok(Mounts(app).add_nas_share(
                    hostgroup=data['name'],
                    local_path=data['local_path'],
                    share_path=data['share_path'],
                    owner = data['owner'],
                    group = data['group'],
                    options=data['options']
                ))
            except ExistsException as e:
                return error(e)
            except Exception as e:
                return error(code=500, message=e)
        else:
            return error('invalid type. must be hostgroups or hosts')

@app.route('/mounts/<string:host_type>/<string:name>', methods = ['GET', 'DELETE'])
def host_index(host_type, name):
    if request.method == 'GET':
        try:
            return ok(Mounts(app).nfs_info[host_type][name])
        except KeyError:
            return not_found()
        except Exception as e:
            return error(e.message)
    elif request.method == 'DELETE':
        try:
            Mounts(app).delete_host_name(host_type=host_type, name=name)
            return ok(f'successfully deleted {name}')
        except KeyError:
            return not_found()
        except Exception as e:
            return error(e.message)
@app.route('/mounts/<string:host_type>/<string:name>/<string:uuid>', methods = ['GET', 'DELETE', 'PATCH'])
def host_mount_index(host_type, name, uuid):
    if request.method == 'GET':
        try:
            return ok([x for x in Mounts(app).nfs_info[host_type][name] if x['uuid'] == uuid])
        except KeyError:
            return not_found()
        except Exception as e:
            return error(e.message)
    elif request.method == 'DELETE':
        try:
            Mounts(app).delete_host_mount(host_type=host_type, name=name, uuid=uuid)
            return ok(f'successfully deleted mount {uuid} for {name}')
        except KeyError:
            return not_found()
        except Exception as e:
            return error(e.message)
    elif request.method == 'PATCH':
        data = {}
        try:
            data = loads(request.data)
        except:
            return error('invalid json body. Please check syntax')
        try:
            if host_type == 'hostgroups':
                return ok(Mounts(app).update_nas_share(
                    uuid=uuid,
                    replacement_dict=data,
                    hostgroup=name))
            elif host_type == 'hosts':
                return ok(Mounts(app).update_nas_share(
                uuid=uuid,
                replacement_dict=data,
                host=name))
        except KeyError:
            return not_found()
        except Exception as e:
            return error(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

