from google.protobuf import timestamp_pb2 as _timestamp_pb2
import common_pb2 as _common_pb2
import message_pb2 as _message_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class TaskState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TASK_STATE_UNSPECIFIED: _ClassVar[TaskState]
    TASK_STATE_SUBMITTED: _ClassVar[TaskState]
    TASK_STATE_WORKING: _ClassVar[TaskState]
    TASK_STATE_COMPLETED: _ClassVar[TaskState]
    TASK_STATE_FAILED: _ClassVar[TaskState]
    TASK_STATE_CANCELLED: _ClassVar[TaskState]
    TASK_STATE_INPUT_REQUIRED: _ClassVar[TaskState]
    TASK_STATE_REJECTED: _ClassVar[TaskState]
    TASK_STATE_AUTH_REQUIRED: _ClassVar[TaskState]

TASK_STATE_UNSPECIFIED: TaskState
TASK_STATE_SUBMITTED: TaskState
TASK_STATE_WORKING: TaskState
TASK_STATE_COMPLETED: TaskState
TASK_STATE_FAILED: TaskState
TASK_STATE_CANCELLED: TaskState
TASK_STATE_INPUT_REQUIRED: TaskState
TASK_STATE_REJECTED: TaskState
TASK_STATE_AUTH_REQUIRED: TaskState

class Task(_message.Message):
    __slots__ = (
        "id",
        "state",
        "messages",
        "artifacts",
        "history",
        "created_at",
        "updated_at",
        "agent_id",
        "context_id",
        "metadata",
        "error",
    )

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    MESSAGES_FIELD_NUMBER: _ClassVar[int]
    ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    id: str
    state: TaskState
    messages: _containers.RepeatedCompositeFieldContainer[_message_pb2.Message]
    artifacts: _containers.RepeatedCompositeFieldContainer[_common_pb2.Artifact]
    history: _containers.RepeatedCompositeFieldContainer[TaskStateTransition]
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    agent_id: str
    context_id: str
    metadata: _containers.ScalarMap[str, str]
    error: _common_pb2.Error
    def __init__(
        self,
        id: _Optional[str] = ...,
        state: _Optional[_Union[TaskState, str]] = ...,
        messages: _Optional[_Iterable[_Union[_message_pb2.Message, _Mapping]]] = ...,
        artifacts: _Optional[_Iterable[_Union[_common_pb2.Artifact, _Mapping]]] = ...,
        history: _Optional[_Iterable[_Union[TaskStateTransition, _Mapping]]] = ...,
        created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        updated_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        agent_id: _Optional[str] = ...,
        context_id: _Optional[str] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
        error: _Optional[_Union[_common_pb2.Error, _Mapping]] = ...,
    ) -> None: ...

class TaskStateTransition(_message.Message):
    __slots__ = ("from_state", "to_state", "timestamp", "reason")
    FROM_STATE_FIELD_NUMBER: _ClassVar[int]
    TO_STATE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    from_state: TaskState
    to_state: TaskState
    timestamp: _timestamp_pb2.Timestamp
    reason: str
    def __init__(
        self,
        from_state: _Optional[_Union[TaskState, str]] = ...,
        to_state: _Optional[_Union[TaskState, str]] = ...,
        timestamp: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...,
        reason: _Optional[str] = ...,
    ) -> None: ...

class SendMessageRequest(_message.Message):
    __slots__ = ("message", "task_id", "session_id", "metadata")

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    message: _message_pb2.Message
    task_id: str
    session_id: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(
        self,
        message: _Optional[_Union[_message_pb2.Message, _Mapping]] = ...,
        task_id: _Optional[str] = ...,
        session_id: _Optional[str] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ("task", "response")
    TASK_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    task: Task
    response: _message_pb2.Message
    def __init__(
        self,
        task: _Optional[_Union[Task, _Mapping]] = ...,
        response: _Optional[_Union[_message_pb2.Message, _Mapping]] = ...,
    ) -> None: ...

class GetTaskRequest(_message.Message):
    __slots__ = ("task_id", "include_messages", "include_artifacts", "include_history")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_MESSAGES_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_ARTIFACTS_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_HISTORY_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    include_messages: bool
    include_artifacts: bool
    include_history: bool
    def __init__(
        self,
        task_id: _Optional[str] = ...,
        include_messages: bool = ...,
        include_artifacts: bool = ...,
        include_history: bool = ...,
    ) -> None: ...

class ListTasksRequest(_message.Message):
    __slots__ = ("states", "limit", "cursor", "agent_id", "context_id")
    STATES_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_ID_FIELD_NUMBER: _ClassVar[int]
    states: _containers.RepeatedScalarFieldContainer[TaskState]
    limit: int
    cursor: str
    agent_id: str
    context_id: str
    def __init__(
        self,
        states: _Optional[_Iterable[_Union[TaskState, str]]] = ...,
        limit: _Optional[int] = ...,
        cursor: _Optional[str] = ...,
        agent_id: _Optional[str] = ...,
        context_id: _Optional[str] = ...,
    ) -> None: ...

class ListTasksResponse(_message.Message):
    __slots__ = ("tasks", "next_cursor", "total_count")
    TASKS_FIELD_NUMBER: _ClassVar[int]
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    tasks: _containers.RepeatedCompositeFieldContainer[Task]
    next_cursor: str
    total_count: int
    def __init__(
        self,
        tasks: _Optional[_Iterable[_Union[Task, _Mapping]]] = ...,
        next_cursor: _Optional[str] = ...,
        total_count: _Optional[int] = ...,
    ) -> None: ...

class CancelTaskRequest(_message.Message):
    __slots__ = ("task_id", "reason")
    TASK_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    task_id: str
    reason: str
    def __init__(self, task_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class CancelTaskResponse(_message.Message):
    __slots__ = ("task", "success")
    TASK_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    task: Task
    success: bool
    def __init__(
        self, task: _Optional[_Union[Task, _Mapping]] = ..., success: bool = ...
    ) -> None: ...
