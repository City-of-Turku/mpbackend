from rest_framework import renderers


class CustomBrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        context["extra_actions"] = None
        context["options_form"] = None
        context["raw_data_post_form"] = None
        return context
