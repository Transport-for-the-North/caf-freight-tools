{{ fullname | escape | underline }}
.. automodule:: {{ fullname }}
   :members:

   {% block classes %}
   {% if classes %}
   Classes
   -------
   {{ fullname }} module contains the following classes (see `Documentation`_ for more details):
   {% for item in classes %}
   - {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block exceptions %}
   {% if exceptions %}
   Exceptions
   ----------
   {{ fullname }} module contains the following exceptions (see `Documentation`_ for more details):
   {% for item in exceptions %}
   - {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block functions %}
   {% if functions %}
   Functions
   ---------
   {{ fullname }} module contains the following functions (see `Documentation`_ for more details):
   {% for item in functions %}
   - {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   Constants
   ---------
   {{ fullname }} module contains the following constants (see `Documentation`_ for more details):
   {% for item in attributes %}
   {%- if item not in inherited_members %}
   .. autoattribute:: {{ name}}.{{ item }}
   {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block docs %}
   {% if classes or functions or exceptions %}
   Documentation
   -------------
   Documentation of classes, functions or exceptions in {{ fullname }} module.
   {% endif %}
   {% endblock %}

