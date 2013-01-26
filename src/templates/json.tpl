[
    {% for post in posts[:-1] %}
    {
        "post_id": "{{ post.post_id }}" ,
        "timestamp": {{ post.timestamp }},
        "origin":  "{{ post.origin }}", 
        "content_type": "{{ post.content_type }}" ,
        "content_string": "{{ post.content_string }}",
        "source": "{{ post.source }}",
        "tags": [],
        "reference": "{{ post.reference }}",
        "signature": "{{ post.signature }}"
    },
    {% endfor %}
    {
        "post_id": "{{ posts[-1].post_id }}" ,
        "timestamp": {{ posts[-1].timestamp }},
        "origin":  "{{ posts[-1].origin }}", 
        "content_type": "{{ posts[-1].content_type }}" ,
        "content_string": "{{ posts[-1].content_string }}",
        "source": "{{ posts[-1].source }}",
        "tags": [],
        "reference": "{{ posts[-1].reference }}",
        "signature": "{{ posts[-1].signature }}"
    }
]
