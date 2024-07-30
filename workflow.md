# EUDAMED API Workflow

## Overview

This document outlines the workflow for interacting with the EUDAMED (European Database on Medical Devices) API to retrieve information about companies, devices, and countries.

## API Endpoints

### 1. Get All Companies by ISO Country Code
- **URL**: `https://ec.europa.eu/tools/eudamed/api/eos`
- **Method**: GET
- **Parameters**:
  - `page`: 0 (starting page)
  - `pageSize`: 25 (items per page)
  - `size`: 1 (not sure about the difference with pageSize)
  - `rnd`: 1718288423623 (random number, possibly for cache busting)
  - `sort`: srn,ASC and versionNumber,DESC
  - `countryIso2Code`: AT (example)
  - `languageIso2Code`: en
- **Max Size**: 300 items per page
- **Status**: GOT_COMPANY_ID

### 2. Get Full Company Details
- **URL**: `https://ec.europa.eu/tools/eudamed/api/actors/{company_id}/publicInformation`
- **Method**: GET
- **Parameters**:
  - `languageIso2Code`: en
- **Note**: This call also retrieves contact information
- **Status**: GOT_COMPANY_DETAILS

### 3. Get Devices of an Economic Operator
- **URL**: `https://ec.europa.eu/tools/eudamed/api/devices/udiDiData`
- **Method**: GET
- **Parameters**:
  - `page`: 0
  - `pageSize`: 25
  - `size`: 25
  - `iso2Code`: en
  - `srn`: DE-AR-000000085 (example)
  - `deviceStatusCode`: refdata.device-model-status.on-the-market
  - `languageIso2Code`: en
- **Status**: GOT_COMPANY_DEVICES

### 4. Get Specific Device Data
- **URL**: `https://ec.europa.eu/tools/eudamed/api/devices/basicUdiData/udiDiData/{device_id}`
- **Method**: GET
- **Parameters**:
  - `languageIso2Code`: en
- **Status**: GOT_COMPANY_DEVICES_DETAILS

### 5. Get All Countries
- **URL**: `https://ec.europa.eu/tools/eudamed/api/countries`
- **Method**: GET
- **Parameters**:
  - `languageIso2Code`: en

## Workflow Steps

1. **COMPANY_ID**: Retrieve list of companies
2. **COMPANY_DETAILS**: Get detailed information for each company
3. **COMPANY_DEVICE_ID**: Fetch devices associated with a company
4. **COMPANY_DEVICE_DETAILS**: Retrieve detailed information for each device

Each step has a corresponding status that can be used to track progress through the workflow.

