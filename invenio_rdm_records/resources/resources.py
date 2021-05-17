# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2021 data-futures.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Bibliographic Record Resource."""

from functools import partial

from flask import abort, g
from flask.globals import request
from flask_resources import MarshmallowJSONSerializer, ResponseHandler, \
    resource_requestctx, response_handler, route, with_content_negotiation
from invenio_drafts_resources.resources import RecordResource
from invenio_records_resources.resources.records.resource import \
    request_data, request_headers, request_search_args, request_view_args

from .serializers import IIIFPresiSchema

with_iiif_content_negotiation = with_content_negotiation(
    response_handlers={
        "application/ld+json": ResponseHandler(
            MarshmallowJSONSerializer(schema_cls=IIIFPresiSchema)),
    },
    default_accept_mimetype='application/ld+json',
)


class RDMRecordResource(RecordResource):
    """RDM record resource."""

    def create_url_rules(self):
        """Create the URL rules for the record resource."""

        def p(route):
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        routes = self.config.routes
        url_rules = super().create_url_rules()
        url_rules += [
            route("POST", p(routes["item-pids-reserve"]), self.pids_reserve),
            route("DELETE", p(routes["item-pids-reserve"]), self.pids_discard),
            route("GET", p(routes["item-review"]), self.review_read),
            route("PUT", p(routes["item-review"]), self.review_update),
            route("DELETE", p(routes["item-review"]), self.review_delete),
            route("POST", p(routes["item-actions-review"]), self.review_submit)
            route(
                "GET",
                p(routes["item-iiif-manifest"]),
                partial(self.read_iiif_manifest, draft=False),
                apply_decorators=False
            ),
            route(
                "GET",
                p(routes["item-draft-iiif-manifest"]),
                partial(self.read_iiif_manifest, draft=True),
                apply_decorators=False
            ),
        ]

        return url_rules

    #
    # Review request
    #
    @request_view_args
    @response_handler()  # TODO: probably needs to change
    def review_read(self):
        """Read the related review request."""
        item = self.service.review.read(
            resource_requestctx.view_args["pid_value"],
            g.identity,
        )

        return item.to_dict(), 200

    @request_headers
    @request_view_args
    @request_data  # TODO: probably needs to change
    def review_update(self):
        """Update a review request."""
        item = self.service.review.update(
            resource_requestctx.view_args["pid_value"],
            g.identity,
            resource_requestctx.data,
            revision_id=resource_requestctx.headers.get("if_match"),
        )

        return item.to_dict(), 200

    @request_headers
    @request_view_args
    def review_delete(self):
        """Delete a review request."""
        self.service.review.delete(
            resource_requestctx.view_args["pid_value"],
            g.identity,
            revision_id=resource_requestctx.headers.get("if_match"),
        )
        return "", 204

    @request_headers
    @request_view_args
    @request_data
    @response_handler()  # TODO: probably needs to change
    def review_submit(self):
        """Submit a draft for review."""
        item = self.service.review.submit(
            resource_requestctx.view_args["pid_value"],
            g.identity,
            resource_requestctx.data,
        )

        return item.to_dict(), 202

    #
    # PIDs
    #
    @request_view_args
    @response_handler()
    def pids_reserve(self):
        """Reserve a PID."""
        item = self.service.pids.create(
            id_=resource_requestctx.view_args["pid_value"],
            scheme=resource_requestctx.view_args["scheme"],
            identity=g.identity,
        )

        return item.to_dict(), 201

    @request_view_args
    @response_handler()
    def pids_discard(self):
        """Discard a previously reserved PID."""
        item = self.service.pids.discard(
            id_=resource_requestctx.view_args["pid_value"],
            scheme=resource_requestctx.view_args["scheme"],
            identity=g.identity,
        )

        return item.to_dict(), 200

    #
    # IIIF Manifest - not all clients support content-negotiation so we need a
    # full endpoint.
    #
    @cross_origin(origin="*", methods=["GET"])
    @with_iiif_content_negotiation
    @request_view_args
    @response_handler()
    def read_iiif_manifest(self, draft=False):
        """Return IIIF Manifest."""
        pid = resource_requestctx.view_args["pid_value"]
        read = self.service.read_draft if draft else self.service.read
        record = read(id_=pid, identity=g.identity)
        return record, 200


#
# Parent Record Links
#
class RDMParentRecordLinksResource(RecordResource):
    """Secret links resource."""

    def create_url_rules(self):
        """Create the URL rules for the record resource."""

        def p(route):
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        routes = self.config.routes
        return [
            route("GET", p(routes["list"]), self.search),
            route("POST", p(routes["list"]), self.create),
            route("GET", p(routes["item"]), self.read),
            route("PUT", p(routes["item"]), self.update),
            route("PATCH", p(routes["item"]), self.partial_update),
            route("DELETE", p(routes["item"]), self.delete),
        ]

    @request_view_args
    @request_data
    @response_handler()
    def create(self):
        """Create a secret link for a record."""
        item = self.service.secret_links.create(
            id_=resource_requestctx.view_args["pid_value"],
            identity=g.identity,
            data=resource_requestctx.data,
        )

        return item.to_dict(), 201

    @request_view_args
    @response_handler()
    def read(self):
        """Read a secret link for a record."""
        item = self.service.secret_links.read(
            id_=resource_requestctx.view_args["pid_value"],
            identity=g.identity,
            link_id=resource_requestctx.view_args["link_id"],
        )
        return item.to_dict(), 200

    def update(self):
        """Update a secret link for a record."""
        abort(405)

    @request_view_args
    @request_data
    @response_handler()
    def partial_update(self):
        """Patch a secret link for a record."""
        item = self.service.secret_links.update(
            id_=resource_requestctx.view_args["pid_value"],
            identity=g.identity,
            link_id=resource_requestctx.view_args["link_id"],
            data=resource_requestctx.data,
        )
        return item.to_dict(), 200

    @request_view_args
    def delete(self):
        """Delete a a secret link for a record."""
        self.service.secret_links.delete(
            id_=resource_requestctx.view_args["pid_value"],
            identity=g.identity,
            link_id=resource_requestctx.view_args["link_id"],
        )
        return "", 204

    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search(self):
        """List secret links for a record."""
        items = self.service.secret_links.read_all(
            id_=resource_requestctx.view_args["pid_value"],
            identity=g.identity,
        )
        return items.to_dict(), 200
