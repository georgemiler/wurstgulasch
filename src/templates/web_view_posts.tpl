<html>
<head>
</head>
<body>
<ul>
{% for post in posts %}
<item> {{post.post_id}}: <br>
{% if post.content_type == "image" %}
<img src="{{post.content_string}}"><br>
{% endif %}
{%endfor%}
</ul>
</body>
</html>
