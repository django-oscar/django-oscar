Mark-up guide
=============

Forms
-----

Forms should be marked-up as::

    <form method="post" action="." class="form-horizontal">
        {% csrf_token %}
        {% include 'partials/form_fields.html' %}
        <div class="form-group col-sm-offset-4 col-sm-8">
            <button class="btn btn-lg btn-primary" type="submit" data-loading-text="{% trans 'Saving...' %}">Save</button>
            or <a href="{{ some_url }}">cancel</a>
        </div>
    </form>

The ``.col-sm-offset-4`` class aligns the buttons with the fields.

Alternatively, use::
    
    <form method="post" action="." class="form-horizontal">
        {% csrf_token %}
        {% include 'partials/form_fields.html' %}
        <div class="control-group">
            <div class="controls">
                <button class="btn btn-lg btn-primary" type="submit" data-loading-text="{% trans 'Saving...' %}">Save</button>
                or <a href="{{ some_url }}">cancel</a>
            </div>
        </div>
    </form>

The ``.control-group`` class aligns the buttons with the fields.
