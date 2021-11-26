# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 data-futures.
# Copyright (C) 2022 Esteban J. G. Gabancho
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""IIIF Presentation API Schema for Invenio RDM Records."""

from flask_resources.serializers import MarshmallowJSONSerializer

from .schema import IIIFPresiSchemaV2

class IIIFPresiV2JSONSerializer(MarshmallowJSONSerializer):
    """Marshmallow based IIIF Presi serializer for records."""


    def __init__(self, **options):
        """Constructor."""
        super().__init__(schema_cls=IIIFPresiSchemaV2, **options)
