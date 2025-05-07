import json
class YoutubeVideoInfo:
    # Define allowed fields
    allowed_fields = {
        #video
        'id':str, 
        'title':str, 
        'fulltitle':str,
        'thumbnail':str, 
        'thumbnails':list, 
        'description':str, 
        'duration':int,
        'duration_string':str,
        'view_count':int, 
        'average_rating':int, 
        'age_limit':int, 
        'webpage_url':str,
        'categories':list, 
        'tags':list, 
        #'automatic_captions':dict, 
        #'subtitles':dict,
        'comment_count':int,
        'chapters':list,
        'heatmap':list,
        'like_count':int, 
        'cn_subtitle_url':str,
        'en_subtitle_url':str,

        #channel
        'channel_id':str, 
        'channel_url':str, 
        'channel':str,
        'channel_follower_count':int,

        #upload info
        'uploader':str,
        'uploader_id':str, 
        'uploader_url':str,
        'upload_date':str,
        'timestamp':int, 

        #other
        'original_url':str,
        'webpage_url_basename':str,
        'webpage_url_domain':str,
        'extractor':str,
        'extractor_key':str,
    }

    def __init__(self, info: dict):
        self.properties = {}
        for key, expected_type in self.allowed_fields.items():
            value = info.get(key, None)
            # Optional: check type if value is not None
            if value is not None and not isinstance(value, expected_type):
                raise TypeError(f"Field '{key}' must be {expected_type.__name__}, got {type(value).__name__}")
            self.properties[key] = value  # Allow None if not provided


    def __getattr__(self, name):
        return self.properties.get(name, None)

    def set_property(self, name, value):
        if name not in self.allowed_fields:
            raise ValueError(f"Invalid field: '{name}'")
        expected_type = self.allowed_fields[name]
        if value is not None and not isinstance(value, expected_type):
            raise TypeError(f"Field '{name}' must be {expected_type.__name__}, got {type(value).__name__}")
        self.properties[name] = value

    def __repr__(self):
        return f"YoutubeVideoInfo({self.properties})"
    
    def to_json(self, indent=None, ensure_ascii=False):
        return json.dumps( self.properties,  indent=indent,  ensure_ascii = ensure_ascii )