
## Overview

### Use this url to get all companies by iso_country code:
https://ec.europa.eu/tools/eudamed/api/eos?page=0&pageSize=25&size=1&rnd=1718288423623&sort=srn,ASC&sort=versionNumber,DESC&countryIso2Code=AT&languageIso2Code=en

Size: how many per page. Max is 300
pageSize: Not sure
status: GOT_COMPANY_ID

### Get the full details of a company
https://ec.europa.eu/tools/eudamed/api/actors/fc9cb447-d565-4643-980b-196ef56fbb6e/publicInformation?languageIso2Code=en
We need this call to also get the contacts. 
status: GOT_COMPANY_DETAILS

### Url to get devices of a economic operator
https://ec.europa.eu/tools/eudamed/api/devices/udiDiData?page=0&pageSize=25&size=25&iso2Code=en&srn=DE-AR-000000085&deviceStatusCode=refdata.device-model-status.on-the-market&languageIso2Code=en
status: GOT_COMPANY_DEVICES


### Get specific device data
https://ec.europa.eu/tools/eudamed/api/devices/basicUdiData/udiDiData/e28ab15c-5051-4d23-83f7-8b265ce6e92c?languageIso2Code=en
status: GOT_COMPANY_DEVICES_DETAILS

### Get all countries
https://ec.europa.eu/tools/eudamed/api/countries?languageIso2Code=en


## Flow
Each step has a status: 
- Step 1. COMPANY_ID
- Step 2. COMPANY_DETAILS
- Step 3. COMPANY_DEVICE_ID
- Step 4. COMPANY_DEVICE_DETAILS

