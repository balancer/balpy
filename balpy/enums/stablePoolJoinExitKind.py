from enum import IntEnum

class StablePoolJoinKind(IntEnum):
  INIT = 0
  EXACT_TOKENS_IN_FOR_BPT_OUT = 1
  TOKEN_IN_FOR_EXACT_BPT_OUT = 2

class StablePhantomPoolJoinKind(IntEnum):
  INIT = 0
  COLLECT_PROTOCOL_FEES = 1

class StablePoolExitKind(IntEnum):
  EXACT_BPT_IN_FOR_ONE_TOKEN_OUT = 0
  EXACT_BPT_IN_FOR_TOKENS_OUT = 1
  BPT_IN_FOR_EXACT_TOKENS_OUT = 2