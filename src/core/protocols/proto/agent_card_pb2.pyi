from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SecuritySchemeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SECURITY_SCHEME_TYPE_UNSPECIFIED: _ClassVar[SecuritySchemeType]
    SECURITY_SCHEME_TYPE_API_KEY: _ClassVar[SecuritySchemeType]
    SECURITY_SCHEME_TYPE_OAUTH2: _ClassVar[SecuritySchemeType]
    SECURITY_SCHEME_TYPE_OPENID_CONNECT: _ClassVar[SecuritySchemeType]
    SECURITY_SCHEME_TYPE_MTLS: _ClassVar[SecuritySchemeType]
    SECURITY_SCHEME_TYPE_HTTP_BEARER: _ClassVar[SecuritySchemeType]
SECURITY_SCHEME_TYPE_UNSPECIFIED: SecuritySchemeType
SECURITY_SCHEME_TYPE_API_KEY: SecuritySchemeType
SECURITY_SCHEME_TYPE_OAUTH2: SecuritySchemeType
SECURITY_SCHEME_TYPE_OPENID_CONNECT: SecuritySchemeType
SECURITY_SCHEME_TYPE_MTLS: SecuritySchemeType
SECURITY_SCHEME_TYPE_HTTP_BEARER: SecuritySchemeType

class AgentCapabilities(_message.Message):
    __slots__ = ("streaming", "push_notifications", "state_transition_history", "supports_extended_agent_card", "extensions")
    STREAMING_FIELD_NUMBER: _ClassVar[int]
    PUSH_NOTIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    STATE_TRANSITION_HISTORY_FIELD_NUMBER: _ClassVar[int]
    SUPPORTS_EXTENDED_AGENT_CARD_FIELD_NUMBER: _ClassVar[int]
    EXTENSIONS_FIELD_NUMBER: _ClassVar[int]
    streaming: bool
    push_notifications: bool
    state_transition_history: bool
    supports_extended_agent_card: bool
    extensions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, streaming: bool = ..., push_notifications: bool = ..., state_transition_history: bool = ..., supports_extended_agent_card: bool = ..., extensions: _Optional[_Iterable[str]] = ...) -> None: ...

class AgentSkill(_message.Message):
    __slots__ = ("id", "name", "description", "input_schema", "output_schema", "examples", "tags")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    INPUT_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_SCHEMA_FIELD_NUMBER: _ClassVar[int]
    EXAMPLES_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    description: str
    input_schema: _struct_pb2.Struct
    output_schema: _struct_pb2.Struct
    examples: _containers.RepeatedCompositeFieldContainer[SkillExample]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., input_schema: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., output_schema: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., examples: _Optional[_Iterable[_Union[SkillExample, _Mapping]]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class SkillExample(_message.Message):
    __slots__ = ("input", "output", "description")
    INPUT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    input: _struct_pb2.Struct
    output: _struct_pb2.Struct
    description: str
    def __init__(self, input: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., output: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., description: _Optional[str] = ...) -> None: ...

class SecurityScheme(_message.Message):
    __slots__ = ("type", "name", "description", "oauth2", "oidc")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    OAUTH2_FIELD_NUMBER: _ClassVar[int]
    OIDC_FIELD_NUMBER: _ClassVar[int]
    type: SecuritySchemeType
    name: str
    description: str
    oauth2: OAuth2Config
    oidc: OpenIDConnectConfig
    def __init__(self, type: _Optional[_Union[SecuritySchemeType, str]] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., oauth2: _Optional[_Union[OAuth2Config, _Mapping]] = ..., oidc: _Optional[_Union[OpenIDConnectConfig, _Mapping]] = ...) -> None: ...

class OAuth2Config(_message.Message):
    __slots__ = ("authorization_url", "token_url", "refresh_url", "scopes", "grant_types", "pkce_required")
    class ScopesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AUTHORIZATION_URL_FIELD_NUMBER: _ClassVar[int]
    TOKEN_URL_FIELD_NUMBER: _ClassVar[int]
    REFRESH_URL_FIELD_NUMBER: _ClassVar[int]
    SCOPES_FIELD_NUMBER: _ClassVar[int]
    GRANT_TYPES_FIELD_NUMBER: _ClassVar[int]
    PKCE_REQUIRED_FIELD_NUMBER: _ClassVar[int]
    authorization_url: str
    token_url: str
    refresh_url: str
    scopes: _containers.ScalarMap[str, str]
    grant_types: _containers.RepeatedScalarFieldContainer[str]
    pkce_required: bool
    def __init__(self, authorization_url: _Optional[str] = ..., token_url: _Optional[str] = ..., refresh_url: _Optional[str] = ..., scopes: _Optional[_Mapping[str, str]] = ..., grant_types: _Optional[_Iterable[str]] = ..., pkce_required: bool = ...) -> None: ...

class OpenIDConnectConfig(_message.Message):
    __slots__ = ("discovery_url",)
    DISCOVERY_URL_FIELD_NUMBER: _ClassVar[int]
    discovery_url: str
    def __init__(self, discovery_url: _Optional[str] = ...) -> None: ...

class SupportedInterface(_message.Message):
    __slots__ = ("type", "url", "version")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    type: str
    url: str
    version: str
    def __init__(self, type: _Optional[str] = ..., url: _Optional[str] = ..., version: _Optional[str] = ...) -> None: ...

class AgentCardSignature(_message.Message):
    __slots__ = ("protected", "signature", "jku")
    PROTECTED_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    JKU_FIELD_NUMBER: _ClassVar[int]
    protected: str
    signature: str
    jku: str
    def __init__(self, protected: _Optional[str] = ..., signature: _Optional[str] = ..., jku: _Optional[str] = ...) -> None: ...

class AgentCard(_message.Message):
    __slots__ = ("agent_id", "name", "description", "version", "provider", "capabilities", "skills", "supported_interfaces", "security_schemes", "default_input_modes", "default_output_modes", "documentation_url", "terms_of_service_url", "privacy_policy_url", "signatures", "metadata")
    class SecuritySchemesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: SecurityScheme
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[SecurityScheme, _Mapping]] = ...) -> None: ...
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PROVIDER_FIELD_NUMBER: _ClassVar[int]
    CAPABILITIES_FIELD_NUMBER: _ClassVar[int]
    SKILLS_FIELD_NUMBER: _ClassVar[int]
    SUPPORTED_INTERFACES_FIELD_NUMBER: _ClassVar[int]
    SECURITY_SCHEMES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_INPUT_MODES_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_OUTPUT_MODES_FIELD_NUMBER: _ClassVar[int]
    DOCUMENTATION_URL_FIELD_NUMBER: _ClassVar[int]
    TERMS_OF_SERVICE_URL_FIELD_NUMBER: _ClassVar[int]
    PRIVACY_POLICY_URL_FIELD_NUMBER: _ClassVar[int]
    SIGNATURES_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    name: str
    description: str
    version: str
    provider: str
    capabilities: AgentCapabilities
    skills: _containers.RepeatedCompositeFieldContainer[AgentSkill]
    supported_interfaces: _containers.RepeatedCompositeFieldContainer[SupportedInterface]
    security_schemes: _containers.MessageMap[str, SecurityScheme]
    default_input_modes: _containers.RepeatedScalarFieldContainer[str]
    default_output_modes: _containers.RepeatedScalarFieldContainer[str]
    documentation_url: str
    terms_of_service_url: str
    privacy_policy_url: str
    signatures: _containers.RepeatedCompositeFieldContainer[AgentCardSignature]
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, agent_id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., version: _Optional[str] = ..., provider: _Optional[str] = ..., capabilities: _Optional[_Union[AgentCapabilities, _Mapping]] = ..., skills: _Optional[_Iterable[_Union[AgentSkill, _Mapping]]] = ..., supported_interfaces: _Optional[_Iterable[_Union[SupportedInterface, _Mapping]]] = ..., security_schemes: _Optional[_Mapping[str, SecurityScheme]] = ..., default_input_modes: _Optional[_Iterable[str]] = ..., default_output_modes: _Optional[_Iterable[str]] = ..., documentation_url: _Optional[str] = ..., terms_of_service_url: _Optional[str] = ..., privacy_policy_url: _Optional[str] = ..., signatures: _Optional[_Iterable[_Union[AgentCardSignature, _Mapping]]] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...

class GetAgentCardRequest(_message.Message):
    __slots__ = ("agent_id", "include_extended")
    AGENT_ID_FIELD_NUMBER: _ClassVar[int]
    INCLUDE_EXTENDED_FIELD_NUMBER: _ClassVar[int]
    agent_id: str
    include_extended: bool
    def __init__(self, agent_id: _Optional[str] = ..., include_extended: bool = ...) -> None: ...

class GetAgentCardResponse(_message.Message):
    __slots__ = ("card",)
    CARD_FIELD_NUMBER: _ClassVar[int]
    card: AgentCard
    def __init__(self, card: _Optional[_Union[AgentCard, _Mapping]] = ...) -> None: ...
