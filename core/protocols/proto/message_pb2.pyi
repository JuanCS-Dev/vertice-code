from google.protobuf import timestamp_pb2 as _timestamp_pb2
import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MessageRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MESSAGE_ROLE_UNSPECIFIED: _ClassVar[MessageRole]
    MESSAGE_ROLE_USER: _ClassVar[MessageRole]
    MESSAGE_ROLE_AGENT: _ClassVar[MessageRole]
    MESSAGE_ROLE_SYSTEM: _ClassVar[MessageRole]

class StreamEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STREAM_EVENT_TYPE_UNSPECIFIED: _ClassVar[StreamEventType]
    STREAM_EVENT_TYPE_STATUS_UPDATE: _ClassVar[StreamEventType]
    STREAM_EVENT_TYPE_MESSAGE_CHUNK: _ClassVar[StreamEventType]
    STREAM_EVENT_TYPE_ARTIFACT_UPDATE: _ClassVar[StreamEventType]
    STREAM_EVENT_TYPE_ERROR: _ClassVar[StreamEventType]
    STREAM_EVENT_TYPE_HEARTBEAT: _ClassVar[StreamEventType]
MESSAGE_ROLE_UNSPECIFIED: MessageRole
MESSAGE_ROLE_USER: MessageRole
MESSAGE_ROLE_AGENT: MessageRole
MESSAGE_ROLE_SYSTEM: MessageRole
STREAM_EVENT_TYPE_UNSPECIFIED: StreamEventType
STREAM_EVENT_TYPE_STATUS_UPDATE: StreamEventType
STREAM_EVENT_TYPE_MESSAGE_CHUNK: StreamEventType
STREAM_EVENT_TYPE_ARTIFACT_UPDATE: StreamEventType
STREAM_EVENT_TYPE_ERROR: StreamEventType
STREAM_EVENT_TYPE_HEARTBEAT: StreamEventType

class Message(_message.Message):
    __slots__ = ("id", "role", "parts", "timestamp", "context_id", "task_id", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    PARTS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: str
    role: MessageRole
    parts: _containers.RepeatedCompositeFieldContainer[_common_pb2.Part]
    timestamp: _timestamp_pb2.Timestamp
    context_id: str
    task_id: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., role: _Optional[_Union[MessageRole, str]] = ..., parts: _Optional[_Iterable[_Union[_common_pb2.Part, _Mapping]]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., context_id: _Optional[str] = ..., task_id: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StreamChunk(_message.Message):
    __slots__ = ("event_type", "task_id", "sequence", "text_delta", "message", "artifact", "status_update", "error", "timestamp")
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    TEXT_DELTA_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ARTIFACT_FIELD_NUMBER: _ClassVar[int]
    STATUS_UPDATE_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    event_type: StreamEventType
    task_id: str
    sequence: int
    text_delta: str
    message: Message
    artifact: _common_pb2.Artifact
    status_update: TaskStatusUpdate
    error: _common_pb2.Error
    timestamp: _timestamp_pb2.Timestamp
    def __init__(self, event_type: _Optional[_Union[StreamEventType, str]] = ..., task_id: _Optional[str] = ..., sequence: _Optional[int] = ..., text_delta: _Optional[str] = ..., message: _Optional[_Union[Message, _Mapping]] = ..., artifact: _Optional[_Union[_common_pb2.Artifact, _Mapping]] = ..., status_update: _Optional[_Union[TaskStatusUpdate, _Mapping]] = ..., error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ..., timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class TaskStatusUpdate(_message.Message):
    __slots__ = ("state", "message", "progress")
    STATE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    state: str
    message: str
    progress: int
    def __init__(self, state: _Optional[str] = ..., message: _Optional[str] = ..., progress: _Optional[int] = ...) -> None: ...
