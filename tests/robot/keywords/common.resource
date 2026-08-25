*** Settings ***
Library    RequestsLibrary

*** Variables ***
${JAVA_URL}    http://localhost:8080
${PYTHON_URL}    http://localhost:8000
${VALID_TOKEN}    Bearer Taman-ei-p1t1a1s-0lla-na1n-123
${JAVA_TOKEN}    Brearer validation-token-123

*** Keywords ***
Create Authenticated Session Python
    Create Session    python_api    ${PYTHON_URL}

Create Authenticated Session Java
    Create Session    java_api    ${JAVA_URL}

Get Python Headers
    &{headers}=    Create Dictionary    Authorization=${VALID_TOKEN}    Content-Type=application/json
    RETURN    ${headers}

Get Java Headers
    &{headers}=    Create Dictionary    Authorization=${VALID_TOKEN}    Content-Type=application/json
    RETURN    ${headers}
    
