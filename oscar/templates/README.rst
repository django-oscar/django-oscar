Mark-up guide
=============

Forms
-----

Forms should be marked-up as::

    <form method="post" action="." class="form-horizontal">
        {% csrf_token %}
        {% include 'partials/form_fields.html' %}
        <div class="form-actions">
            <button class="btn btn-large btn-primary" type="submit">Save</button>
            or <a href="{{ some_url }}">cancel</a>
        </div>
    </form>

The ``.form-actions`` class aligns the buttons with the fields and adds a gray
background.

Alternatively, use::
    
    <form method="post" action="." class="form-horizontal">
        {% csrf_token %}
        {% include 'partials/form_fields.html' %}
        <div class="control-group">
            <div class="controls">
                <button class="btn btn-large btn-primary" type="submit">Save</button>
                or <a href="{{ some_url }}">cancel</a>
            </div>
        </div>
    </form>

The ``.control-group`` class aligns the buttons with the fields.
