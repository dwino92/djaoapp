# Copyright (c) 2018, DjaoDjin inc.
# see LICENSE

import logging
from functools import wraps

from django import http
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.db import DEFAULT_DB_ALIAS
from django.template.response import TemplateResponse
from django.utils.decorators import available_attrs
from django.utils import six
from multitier.thread_locals import get_current_site
from pages.locals import (enable_instrumentation, disable_instrumentation,
    get_edition_tools_context_data)
from rules.perms import NoRuleMatch, check_matched, redirect_or_denied
from rules.utils import get_current_app
from saas.decorators import (NORMAL, _fail_direct, _fail_provider,
    _fail_provider_only, _fail_self_provider, _has_valid_access)

from .locals import get_current_broker
from .edition_tools import inject_edition_tools as _inject_edition_tools


LOGGER = logging.getLogger(__name__)


def inject_edition_tools(function=None):
    """
    Inject the edition tools into the HTML response.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            enable_instrumentation()
            response = view_func(request, *args, **kwargs)
            disable_instrumentation()
            if isinstance(response, TemplateResponse):
                # We could use ``SingleTemplateResponse`` to catch both
                # django and restframework responses. Unfortunately
                # the content_type on restframework responses is set
                # very late (render), while at the same time django
                # defaults it to text/html until then.
                response.render()
                soup = _inject_edition_tools(response, request,
                    context=get_edition_tools_context_data())
                if soup:
                    # str(soup) instead of soup.prettify() to avoid
                    # trailing whitespace on a reformatted HTML textarea
                    response.content = str(soup)
            return response
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def requires_direct(function=None, roledescription=None, strength=NORMAL,
                    redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Same decorator as ``saas.decorators.requires_direct`` with the additional
    look up for a ``Site`` account.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            try:
                app = get_current_app()
                redirect_url, _, _ = check_matched(request, app,
                    prefixes=[
                        '/api/billing/', '/api/metrics/', '/api/profile/',
                        '/api/users/',
                        '/billing/', '/metrics/', '/profile/', '/users/'])
                if redirect_url:
                    if isinstance(redirect_url, six.string_types):
                        return http.HttpResponseRedirect(redirect_url)
                    raise PermissionDenied()
            except NoRuleMatch:
                slug = kwargs.get('charge', kwargs.get('organization', None))
                redirect_url = _fail_direct(request, organization=slug,
                        roledescription=roledescription, strength=strength)
                if redirect_url:
                    return redirect_or_denied(request, redirect_url,
                        redirect_field_name=redirect_field_name,
                        descr="%(user)s is not a direct manager '\
    ' of %(organization)s." % {'user': request.user, 'organization': slug})

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def requires_provider(function=None, roledescription=None, strength=NORMAL):
    """
    Same decorator as saas.requires_provider with the added permissions
    that managers of the site database itself are also able to access
    profiles of registered yet unsubscribed ``Organization``.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            site = get_current_site()
            organization = kwargs.get('organization', None)
            if site.db_name and site.db_name != DEFAULT_DB_ALIAS:
                # We have a separate database so it is OK for a manager
                # of the site to access registered ``Organization`` which
                # are not subscribed yet.
                if _has_valid_access(
                    request, [get_current_broker()], strength):
                    return view_func(request, *args, **kwargs)
            try:
                app = get_current_app()
                redirect_url, _, _ = check_matched(request, app,
                    prefixes=[
                        '/api/billing/', '/api/metrics/', '/api/profile/',
                        '/api/users/',
                        '/billing/', '/metrics/', '/profile/', '/users/'])
                if redirect_url:
                    if isinstance(redirect_url, six.string_types):
                        return http.HttpResponseRedirect(redirect_url)
                    raise PermissionDenied()
            except NoRuleMatch:
                # By default, we are looking for provider.
                slug = kwargs.get('charge', organization)
                redirect_url = _fail_provider(request, organization=slug,
                    roledescription=roledescription, strength=strength)
                if redirect_url:
                    return redirect_or_denied(request, redirect_url,
                        "%(user)s is neither a manager "\
" for %(slug)s nor a manager of one of %(slug)s providers." % {
    'user': request.user, 'slug': slug})
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def requires_provider_only(function=None, roledescription=None,
                      strength=NORMAL):
    """
    Same decorator as saas.requires_provider with the added permissions
    that managers of the site database itself are also able to access
    profiles of registered yet unsubscribed ``Organization``.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            site = get_current_site()
            organization = kwargs.get('organization', None)
            if site.db_name:
                # We have a separate database so it is OK for a manager
                # of the site to access registered ``Organization`` which
                # are not subscribed yet.
                if _has_valid_access(
                    request, [get_current_broker()], strength):
                    return view_func(request, *args, **kwargs)
            try:
                app = get_current_app()
                redirect_url, _, _ = check_matched(request, app,
                    prefixes=[
                        '/api/billing/', '/api/metrics/', '/api/profile/',
                        '/api/users/',
                        '/billing/', '/metrics/', '/profile/', '/users/'])
                if redirect_url:
                    if isinstance(redirect_url, six.string_types):
                        return http.HttpResponseRedirect(redirect_url)
                    raise PermissionDenied()
            except NoRuleMatch:
                # By default, we are looking for provider.
                slug = kwargs.get('charge', organization)
                redirect_url = _fail_provider_only(request, organization=slug,
                    roledescription=roledescription, strength=strength)
                if redirect_url:
                    return redirect_or_denied(request, redirect_url,
                        "%(user)s is not a manager of one of"\
" %(slug)s providers." % {'user': request.user, 'slug': slug})
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def requires_self_provider(function=None, strength=NORMAL):
    """
    Same decorator as saas.requires_self_provider with the added permissions
    that managers of the site database itself are also able to access
    profiles of registered yet unsubscribed ``Organization``.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            site = get_current_site()
            if site.db_name:
                # We have a separate database so it is OK for a manager
                # of the site to access profiles of ``User`` which
                # are not subscribed yet.
                if _has_valid_access(
                    request, [get_current_broker()], strength):
                    return view_func(request, *args, **kwargs)
            try:
                app = get_current_app()
                redirect_url, _, _ = check_matched(request, app,
                    prefixes=[
                        '/api/billing/', '/api/metrics/', '/api/profile/',
                        '/api/users/',
                        '/billing/', '/metrics/', '/profile/', '/users/'])
                if redirect_url:
                    if isinstance(redirect_url, six.string_types):
                        return http.HttpResponseRedirect(redirect_url)
                    raise PermissionDenied()
            except NoRuleMatch:
                if _fail_self_provider(
                        request, user=kwargs.get('user', None),
                        strength=strength):
                    raise PermissionDenied("%(auth)s has neither a direct"\
" relation to an organization connected to %(user)s nor a connection to one"\
"of the providers to such organization." % {
    'auth': request.user, 'user': kwargs.get('user', None)})
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
