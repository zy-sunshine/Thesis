#!/usr/bin/env python
# -*- coding=utf-8 -*-
from django.conf import settings

def common(request):
    """
    Adds media-related context variables to the context.

    """
    return {'SITE_CONFIG': settings.SITE_CONFIG}
