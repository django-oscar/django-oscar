Mark-up guide
=============

Forms
-----

Forms should be marked-up as::

    <form method="post" action="." class="form-horizontal">
        {% csrf_token %}
        {% include 'partials/form_fields.html' %}
        <div class="form-group form-actions">
            <button class="btn btn-lg btn-primary" type="submit" data-loading-text="{% trans 'Saving...' %}">Save</button>
            or <a href="{{ some_url }}">cancel</a>
        </div>
    </form>

The ``.form-group`` class aligns the buttons with the fields. The ``.forms-actions``
class adds a gray background.

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