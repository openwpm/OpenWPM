from typing import Any, Dict, NewType

from multiprocess import Queue

BrowserParams = NewType("BrowserParams", Dict[str, Any])
ManagerParams = NewType("ManagerParams", Dict[str, Any])
VisitId = NewType("VisitId", int)
BrowserId = NewType("BrowserId", int)
