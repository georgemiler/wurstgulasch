<html>
<head>
</head>
<body>
<ul>
{% for post in posts %}
<li> {{post.post_id}}: <br>
{% if post.content_type == "image" %}
<img src="{{post.content_string}}"><br>
{% endif %}
{{ post.description }} </li>
{%endfor%}
</ul>
</body>
</html>
