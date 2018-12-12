from functools import wraps
from flask import request
import uuid
from wtforms import Form
from wtforms.fields import IntegerField, StringField, FieldList, FormField
from wtforms.validators import InputRequired, Regexp


def validate_pattern_file_schema(schema_cls):
    """ file validator """
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            form = schema_cls(request.form)
            if len(request.files) == 0:
                raise AtomAddPatternFailedError("Pattern file is required field")
            if not form.validate():
                raise AtomBadRequestError(form.errors)
            kwargs['form'] = form
            kwargs['pattern_file'] = request.files['file']
            return func(*args, **kwargs)
        return wrapped_func
    return decorator


class AddPatternForm(Form):
    # TODO: Change vendor_key_id is InputRequired() and from certificate
    vendor_key_id = StringField('vendor_key_id', default=uuid.uuid4())


class DeploymentForm(Form):
    # TODO: Change vendor_key_id is InputRequired() and from certificate
    vendor_key_id = StringField('vendor_key_id', default=uuid.uuid4())
    device = StringField('device', [InputRequired()])


# for svs.patterns API
def validate_json_schema(schema_cls):
    """a naive json validator"""
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            json_data = request.get_json(force=True)
            form = schema_cls.from_json(json_data)
            if not form.validate():
                raise AtomBadRequestError(form.errors)
            kwargs['form'] = form
            return func(*args, **kwargs)
        return wrapped_func
    return decorator


# SVS pattern form

class SyncSvsPatternStaticForm(Form):
    type = IntegerField('type', [InputRequired()])  # 'type' is a class of Python standard library.
    target = StringField('target', [InputRequired()])
    section = StringField('section', [InputRequired(), Regexp('^\.')])
    pattern = StringField('pattern', [InputRequired()])


class SyncSvsPatternForm(Form):
    """
    Example json data
    {
        "static": [
            {
                "type": 1,
                "target": "libvncserver",
                "section": ".rodata",
                "pattern": "LibVNCServer ([0-9]+\\.[0-9]+\\.[0-9]+)"
            },
            {
                "target": "libkrb5",
                "section": ".data",
                "pattern": "krb5-([0-9]+\\.[0-9]+\\.*[0-9]*)"
            },
            {
                "type": 2,
                "target": "tcpdump",
                "section": ".rodata",
                "pattern": "([0-9]+\\.[0-9]+\\.[0-9]+)$"
            }
        ]
    }
    """
    static = FieldList(FormField(SyncSvsPatternStaticForm))

    def validate(self):
        valid = True
        if not Form.validate(self):
            valid = False
        return valid


# Known libraries
class KnownLibrariesForm(Form):
    vendor = StringField('vendor', [InputRequired()])
    app = StringField('app', [InputRequired()])
    libname = StringField('libname', [InputRequired()])


class SyncKnownLibrariesForm(Form):
    known_library_list = FieldList(FormField(KnownLibrariesForm))

