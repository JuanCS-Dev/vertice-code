from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class PartType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PART_TYPE_UNSPECIFIED: _ClassVar[PartType]
    PART_TYPE_TEXT: _ClassVar[PartType]
    PART_TYPE_FILE: _ClassVar[PartType]
    PART_TYPE_DATA: _ClassVar[PartType]

class ErrorSeverity(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERROR_SEVERITY_UNSPECIFIED: _ClassVar[ErrorSeverity]
    ERROR_SEVERITY_INFO: _ClassVar[ErrorSeverity]
    ERROR_SEVERITY_WARNING: _ClassVar[ErrorSeverity]
    ERROR_SEVERITY_ERROR: _ClassVar[ErrorSeverity]
    ERROR_SEVERITY_FATAL: _ClassVar[ErrorSeverity]

PART_TYPE_UNSPECIFIED: PartType
PART_TYPE_TEXT: PartType
PART_TYPE_FILE: PartType
PART_TYPE_DATA: PartType
ERROR_SEVERITY_UNSPECIFIED: ErrorSeverity
ERROR_SEVERITY_INFO: ErrorSeverity
ERROR_SEVERITY_WARNING: ErrorSeverity
ERROR_SEVERITY_ERROR: ErrorSeverity
ERROR_SEVERITY_FATAL: ErrorSeverity

class TextPart(_message.Message):
    __slots__ = ("text", "mime_type")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    text: str
    mime_type: str
    def __init__(self, text: _Optional[str] = ..., mime_type: _Optional[str] = ...) -> None: ...

class FilePart(_message.Message):
    __slots__ = ("name", "mime_type", "inline_data", "uri")
    NAME_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    INLINE_DATA_FIELD_NUMBER: _ClassVar[int]
    URI_FIELD_NUMBER: _ClassVar[int]
    name: str
    mime_type: str
    inline_data: bytes
    uri: str
    def __init__(
        self,
        name: _Optional[str] = ...,
        mime_type: _Optional[str] = ...,
        inline_data: _Optional[bytes] = ...,
        uri: _Optional[str] = ...,
    ) -> None: ...

class DataPart(_message.Message):
    __slots__ = ("schema", "data")
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    schema: str
    data: _struct_pb2.Struct
    def __init__(
        self,
        schema: _Optional[str] = ...,
        data: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...,
    ) -> None: ...

class Part(_message.Message):
    __slots__ = ("type", "text", "file", "data", "metadata")

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    TYPE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    type: PartType
    text: TextPart
    file: FilePart
    data: DataPart
    metadata: _containers.ScalarMap[str, str]
    def __init__(
        self,
        type: _Optional[_Union[PartType, str]] = ...,
        text: _Optional[_Union[TextPart, _Mapping]] = ...,
        file: _Optional[_Union[FilePart, _Mapping]] = ...,
        data: _Optional[_Union[DataPart, _Mapping]] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class Artifact(_message.Message):
    __slots__ = ("id", "name", "mime_type", "inline_data", "uri", "created_at", "metadata")

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MIME_TYPE_FIELD_NUMBER: _ClassVar[int]
    INLINE_DATA_FIELD_NUMBER: _ClassVar[int]
    URI_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    mime_type: str
    inline_data: bytes
    uri: str
    created_at: _timestamp_pb2.Timestamp
    metadata: _containers.ScalarMap[str, str]
    def __init__(
        self,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        mime_type: _Optional[str] = ...,
        inline_data: _Optional[bytes] = ...,
        uri: _Optional[str] = ...,
        created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class Error(_message.Message):
    __slots__ = ("code", "message", "severity", "details")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    severity: ErrorSeverity
    details: _struct_pb2.Struct
    def __init__(
        self,
        code: _Optional[int] = ...,
        message: _Optional[str] = ...,
        severity: _Optional[_Union[ErrorSeverity, str]] = ...,
        details: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...,
    ) -> None: ...
