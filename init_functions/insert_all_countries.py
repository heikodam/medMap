import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

# List of all countries with ISO codes and names

countries = [ 
    {
    "name" : "Afghanistan",
    "type" : "NON_EU",
    "iso2Code" : "AF",
    "nonEUMemberState" : True
    }, {
    "name" : "Albania",
    "type" : "NON_EU",
    "iso2Code" : "AL",
    "nonEUMemberState" : True
    }, {
    "name" : "Algeria",
    "type" : "NON_EU",
    "iso2Code" : "DZ",
    "nonEUMemberState" : True
    }, {
    "name" : "American Samoa",
    "type" : "NON_EU",
    "iso2Code" : "AS",
    "nonEUMemberState" : True
    }, {
    "name" : "Andorra",
    "type" : "NON_EU",
    "iso2Code" : "AD",
    "nonEUMemberState" : True
    }, {
    "name" : "Angola",
    "type" : "NON_EU",
    "iso2Code" : "AO",
    "nonEUMemberState" : True
    }, {
    "name" : "Anguilla",
    "type" : "NON_EU",
    "iso2Code" : "AI",
    "nonEUMemberState" : True
    }, {
    "name" : "Antarctica",
    "type" : "NON_EU",
    "iso2Code" : "AQ",
    "nonEUMemberState" : True
    }, {
    "name" : "Antigua and Barbuda",
    "type" : "NON_EU",
    "iso2Code" : "AG",
    "nonEUMemberState" : True
    }, {
    "name" : "Argentina",
    "type" : "NON_EU",
    "iso2Code" : "AR",
    "nonEUMemberState" : True
    }, {
    "name" : "Armenia",
    "type" : "NON_EU",
    "iso2Code" : "AM",
    "nonEUMemberState" : True
    }, {
    "name" : "Aruba",
    "type" : "NON_EU",
    "iso2Code" : "AW",
    "nonEUMemberState" : True
    }, {
    "name" : "Australia",
    "type" : "NON_EU",
    "iso2Code" : "AU",
    "nonEUMemberState" : True
    }, {
    "name" : "Austria",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "AT",
    "nonEUMemberState" : False
    }, {
    "name" : "Azerbaijan",
    "type" : "NON_EU",
    "iso2Code" : "AZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Bahamas",
    "type" : "NON_EU",
    "iso2Code" : "BS",
    "nonEUMemberState" : True
    }, {
    "name" : "Bahrain",
    "type" : "NON_EU",
    "iso2Code" : "BH",
    "nonEUMemberState" : True
    }, {
    "name" : "Bangladesh",
    "type" : "NON_EU",
    "iso2Code" : "BD",
    "nonEUMemberState" : True
    }, {
    "name" : "Barbados",
    "type" : "NON_EU",
    "iso2Code" : "BB",
    "nonEUMemberState" : True
    }, {
    "name" : "Belarus",
    "type" : "NON_EU",
    "iso2Code" : "BY",
    "nonEUMemberState" : True
    }, {
    "name" : "Belgium",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "BE",
    "nonEUMemberState" : False
    }, {
    "name" : "Belize",
    "type" : "NON_EU",
    "iso2Code" : "BZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Benin",
    "type" : "NON_EU",
    "iso2Code" : "BJ",
    "nonEUMemberState" : True
    }, {
    "name" : "Bermuda",
    "type" : "NON_EU",
    "iso2Code" : "BM",
    "nonEUMemberState" : True
    }, {
    "name" : "Bhutan",
    "type" : "NON_EU",
    "iso2Code" : "BT",
    "nonEUMemberState" : True
    }, {
    "name" : "Bolivia",
    "type" : "NON_EU",
    "iso2Code" : "BO",
    "nonEUMemberState" : True
    }, {
    "name" : "Bosnia and Herzegovina",
    "type" : "NON_EU",
    "iso2Code" : "BA",
    "nonEUMemberState" : True
    }, {
    "name" : "Botswana",
    "type" : "NON_EU",
    "iso2Code" : "BW",
    "nonEUMemberState" : True
    }, {
    "name" : "Bouvet Island",
    "type" : "NON_EU",
    "iso2Code" : "BV",
    "nonEUMemberState" : True
    }, {
    "name" : "Brazil",
    "type" : "NON_EU",
    "iso2Code" : "BR",
    "nonEUMemberState" : True
    }, {
    "name" : "British Virgin Islands",
    "type" : "NON_EU",
    "iso2Code" : "VG",
    "nonEUMemberState" : True
    }, {
    "name" : "Brunei Darussalam",
    "type" : "NON_EU",
    "iso2Code" : "BN",
    "nonEUMemberState" : True
    }, {
    "name" : "Bulgaria",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "BG",
    "nonEUMemberState" : False
    }, {
    "name" : "Burkina Faso",
    "type" : "NON_EU",
    "iso2Code" : "BF",
    "nonEUMemberState" : True
    }, {
    "name" : "Burundi",
    "type" : "NON_EU",
    "iso2Code" : "BI",
    "nonEUMemberState" : True
    }, {
    "name" : "Cambodia",
    "type" : "NON_EU",
    "iso2Code" : "KH",
    "nonEUMemberState" : True
    }, {
    "name" : "Cameroon",
    "type" : "NON_EU",
    "iso2Code" : "CM",
    "nonEUMemberState" : True
    }, {
    "name" : "Canada",
    "type" : "NON_EU",
    "iso2Code" : "CA",
    "nonEUMemberState" : True
    }, {
    "name" : "Cape Verde",
    "type" : "NON_EU",
    "iso2Code" : "CV",
    "nonEUMemberState" : True
    }, {
    "name" : "Cayman Islands",
    "type" : "NON_EU",
    "iso2Code" : "KY",
    "nonEUMemberState" : True
    }, {
    "name" : "Central African",
    "type" : "NON_EU",
    "iso2Code" : "CF",
    "nonEUMemberState" : True
    }, {
    "name" : "Chad",
    "type" : "NON_EU",
    "iso2Code" : "TD",
    "nonEUMemberState" : True
    }, {
    "name" : "Chile",
    "type" : "NON_EU",
    "iso2Code" : "CL",
    "nonEUMemberState" : True
    }, {
    "name" : "China",
    "type" : "NON_EU",
    "iso2Code" : "CN",
    "nonEUMemberState" : True
    }, {
    "name" : "Christmas Island",
    "type" : "NON_EU",
    "iso2Code" : "CX",
    "nonEUMemberState" : True
    }, {
    "name" : "Cocos (Keeling) Islands",
    "type" : "NON_EU",
    "iso2Code" : "CC",
    "nonEUMemberState" : True
    }, {
    "name" : "Colombia",
    "type" : "NON_EU",
    "iso2Code" : "CO",
    "nonEUMemberState" : True
    }, {
    "name" : "Comoros",
    "type" : "NON_EU",
    "iso2Code" : "KM",
    "nonEUMemberState" : True
    }, {
    "name" : "Cook Islands",
    "type" : "NON_EU",
    "iso2Code" : "CK",
    "nonEUMemberState" : True
    }, {
    "name" : "Costa Rica",
    "type" : "NON_EU",
    "iso2Code" : "CR",
    "nonEUMemberState" : True
    }, {
    "name" : "Croatia",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "HR",
    "nonEUMemberState" : False
    }, {
    "name" : "Cuba",
    "type" : "NON_EU",
    "iso2Code" : "CU",
    "nonEUMemberState" : True
    }, {
    "name" : "Cyprus",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "CY",
    "nonEUMemberState" : False
    }, {
    "name" : "Czechia",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "CZ",
    "nonEUMemberState" : False
    }, {
    "name" : "Côte d'Ivoire",
    "type" : "NON_EU",
    "iso2Code" : "CI",
    "nonEUMemberState" : True
    }, {
    "name" : "Democratic People's Republic of Korea",
    "type" : "NON_EU",
    "iso2Code" : "KP",
    "nonEUMemberState" : True
    }, {
    "name" : "Denmark",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "DK",
    "nonEUMemberState" : False
    }, {
    "name" : "Djibouti",
    "type" : "NON_EU",
    "iso2Code" : "DJ",
    "nonEUMemberState" : True
    }, {
    "name" : "Dominica",
    "type" : "NON_EU",
    "iso2Code" : "DM",
    "nonEUMemberState" : True
    }, {
    "name" : "Dominican Republic",
    "type" : "NON_EU",
    "iso2Code" : "DO",
    "nonEUMemberState" : True
    }, {
    "name" : "Ecuador",
    "type" : "NON_EU",
    "iso2Code" : "EC",
    "nonEUMemberState" : True
    }, {
    "name" : "Egypt",
    "type" : "NON_EU",
    "iso2Code" : "EG",
    "nonEUMemberState" : True
    }, {
    "name" : "El Salvador",
    "type" : "NON_EU",
    "iso2Code" : "SV",
    "nonEUMemberState" : True
    }, {
    "name" : "Equatorial Guinea",
    "type" : "NON_EU",
    "iso2Code" : "GQ",
    "nonEUMemberState" : True
    }, {
    "name" : "Eritrea",
    "type" : "NON_EU",
    "iso2Code" : "ER",
    "nonEUMemberState" : True
    }, {
    "name" : "Estonia",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "EE",
    "nonEUMemberState" : False
    }, {
    "name" : "Eswatini",
    "type" : "NON_EU",
    "iso2Code" : "SZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Ethiopia",
    "type" : "NON_EU",
    "iso2Code" : "ET",
    "nonEUMemberState" : True
    }, {
    "name" : "Falkland Islands",
    "type" : "NON_EU",
    "iso2Code" : "FK",
    "nonEUMemberState" : True
    }, {
    "name" : "Faroe Islands",
    "type" : "NON_EU",
    "iso2Code" : "FO",
    "nonEUMemberState" : True
    }, {
    "name" : "Federated States of Micronesia",
    "type" : "NON_EU",
    "iso2Code" : "FM",
    "nonEUMemberState" : True
    }, {
    "name" : "Fiji",
    "type" : "NON_EU",
    "iso2Code" : "FJ",
    "nonEUMemberState" : True
    }, {
    "name" : "Finland",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "FI",
    "nonEUMemberState" : False
    }, {
    "name" : "France",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "FR",
    "nonEUMemberState" : False
    }, {
    "name" : "French Polynesia",
    "type" : "NON_EU",
    "iso2Code" : "PF",
    "nonEUMemberState" : True
    }, {
    "name" : "French Southern Territories",
    "type" : "NON_EU",
    "iso2Code" : "TF",
    "nonEUMemberState" : True
    }, {
    "name" : "Gabon",
    "type" : "NON_EU",
    "iso2Code" : "GA",
    "nonEUMemberState" : True
    }, {
    "name" : "Gambia",
    "type" : "NON_EU",
    "iso2Code" : "GM",
    "nonEUMemberState" : True
    }, {
    "name" : "Georgia",
    "type" : "NON_EU",
    "iso2Code" : "GE",
    "nonEUMemberState" : True
    }, {
    "name" : "Germany",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "DE",
    "nonEUMemberState" : False
    }, {
    "name" : "Ghana",
    "type" : "NON_EU",
    "iso2Code" : "GH",
    "nonEUMemberState" : True
    }, {
    "name" : "Gibraltar",
    "type" : "NON_EU",
    "iso2Code" : "GI",
    "nonEUMemberState" : True
    }, {
    "name" : "Greece",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "EL",
    "nonEUMemberState" : False
    }, {
    "name" : "Greenland",
    "type" : "NON_EU",
    "iso2Code" : "GL",
    "nonEUMemberState" : True
    }, {
    "name" : "Grenada",
    "type" : "NON_EU",
    "iso2Code" : "GD",
    "nonEUMemberState" : True
    }, {
    "name" : "Guam",
    "type" : "NON_EU",
    "iso2Code" : "GU",
    "nonEUMemberState" : True
    }, {
    "name" : "Guatemala",
    "type" : "NON_EU",
    "iso2Code" : "GT",
    "nonEUMemberState" : True
    }, {
    "name" : "Guernsey",
    "type" : "NON_EU",
    "iso2Code" : "GG",
    "nonEUMemberState" : True
    }, {
    "name" : "Guinea",
    "type" : "NON_EU",
    "iso2Code" : "GN",
    "nonEUMemberState" : True
    }, {
    "name" : "Guinea-Bissau",
    "type" : "NON_EU",
    "iso2Code" : "GW",
    "nonEUMemberState" : True
    }, {
    "name" : "Guyana",
    "type" : "NON_EU",
    "iso2Code" : "GY",
    "nonEUMemberState" : True
    }, {
    "name" : "Haiti",
    "type" : "NON_EU",
    "iso2Code" : "HT",
    "nonEUMemberState" : True
    }, {
    "name" : "Heard Island and McDonald Islands",
    "type" : "NON_EU",
    "iso2Code" : "HM",
    "nonEUMemberState" : True
    }, {
    "name" : "Honduras",
    "type" : "NON_EU",
    "iso2Code" : "HN",
    "nonEUMemberState" : True
    }, {
    "name" : "Hong Kong",
    "type" : "NON_EU",
    "iso2Code" : "HK",
    "nonEUMemberState" : True
    }, {
    "name" : "Hungary",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "HU",
    "nonEUMemberState" : False
    }, {
    "name" : "Iceland",
    "type" : "EU_EXTENDED",
    "iso2Code" : "IS",
    "nonEUMemberState" : False
    }, {
    "name" : "India",
    "type" : "NON_EU",
    "iso2Code" : "IN",
    "nonEUMemberState" : True
    }, {
    "name" : "Indonesia",
    "type" : "NON_EU",
    "iso2Code" : "ID",
    "nonEUMemberState" : True
    }, {
    "name" : "Iraq",
    "type" : "NON_EU",
    "iso2Code" : "IQ",
    "nonEUMemberState" : True
    }, {
    "name" : "Ireland",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "IE",
    "nonEUMemberState" : False
    }, {
    "name" : "Islamic Republic of Iran",
    "type" : "NON_EU",
    "iso2Code" : "IR",
    "nonEUMemberState" : True
    }, {
    "name" : "Isle of Man",
    "type" : "NON_EU",
    "iso2Code" : "IM",
    "nonEUMemberState" : True
    }, {
    "name" : "Israel",
    "type" : "NON_EU",
    "iso2Code" : "IL",
    "nonEUMemberState" : True
    }, {
    "name" : "Italy",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "IT",
    "nonEUMemberState" : False
    }, {
    "name" : "Jamaica",
    "type" : "NON_EU",
    "iso2Code" : "JM",
    "nonEUMemberState" : True
    }, {
    "name" : "Japan",
    "type" : "NON_EU",
    "iso2Code" : "JP",
    "nonEUMemberState" : True
    }, {
    "name" : "Jersey",
    "type" : "NON_EU",
    "iso2Code" : "JE",
    "nonEUMemberState" : True
    }, {
    "name" : "Jordan",
    "type" : "NON_EU",
    "iso2Code" : "JO",
    "nonEUMemberState" : True
    }, {
    "name" : "Kazakhstan",
    "type" : "NON_EU",
    "iso2Code" : "KZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Kenya",
    "type" : "NON_EU",
    "iso2Code" : "KE",
    "nonEUMemberState" : True
    }, {
    "name" : "Kiribati",
    "type" : "NON_EU",
    "iso2Code" : "KI",
    "nonEUMemberState" : True
    }, {
    "name" : "Kuwait",
    "type" : "NON_EU",
    "iso2Code" : "KW",
    "nonEUMemberState" : True
    }, {
    "name" : "Kyrgyzstan",
    "type" : "NON_EU",
    "iso2Code" : "KG",
    "nonEUMemberState" : True
    }, {
    "name" : "Lao People's Democratic Republic",
    "type" : "NON_EU",
    "iso2Code" : "LA",
    "nonEUMemberState" : True
    }, {
    "name" : "Latvia",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "LV",
    "nonEUMemberState" : False
    }, {
    "name" : "Lebanon",
    "type" : "NON_EU",
    "iso2Code" : "LB",
    "nonEUMemberState" : True
    }, {
    "name" : "Lesotho",
    "type" : "NON_EU",
    "iso2Code" : "LS",
    "nonEUMemberState" : True
    }, {
    "name" : "Liberia",
    "type" : "NON_EU",
    "iso2Code" : "LR",
    "nonEUMemberState" : True
    }, {
    "name" : "Libyan Arab Jamahiriya",
    "type" : "NON_EU",
    "iso2Code" : "LY",
    "nonEUMemberState" : True
    }, {
    "name" : "Liechtenstein",
    "type" : "EU_EXTENDED",
    "iso2Code" : "LI",
    "nonEUMemberState" : False
    }, {
    "name" : "Lithuania",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "LT",
    "nonEUMemberState" : False
    }, {
    "name" : "Luxembourg",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "LU",
    "nonEUMemberState" : False
    }, {
    "name" : "Macao",
    "type" : "NON_EU",
    "iso2Code" : "MO",
    "nonEUMemberState" : True
    }, {
    "name" : "Madagascar",
    "type" : "NON_EU",
    "iso2Code" : "MG",
    "nonEUMemberState" : True
    }, {
    "name" : "Malawi",
    "type" : "NON_EU",
    "iso2Code" : "MW",
    "nonEUMemberState" : True
    }, {
    "name" : "Malaysia",
    "type" : "NON_EU",
    "iso2Code" : "MY",
    "nonEUMemberState" : True
    }, {
    "name" : "Maldives",
    "type" : "NON_EU",
    "iso2Code" : "MV",
    "nonEUMemberState" : True
    }, {
    "name" : "Mali",
    "type" : "NON_EU",
    "iso2Code" : "ML",
    "nonEUMemberState" : True
    }, {
    "name" : "Malta",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "MT",
    "nonEUMemberState" : False
    }, {
    "name" : "Marshall Islands",
    "type" : "NON_EU",
    "iso2Code" : "MH",
    "nonEUMemberState" : True
    }, {
    "name" : "Mauritania",
    "type" : "NON_EU",
    "iso2Code" : "MR",
    "nonEUMemberState" : True
    }, {
    "name" : "Mauritius",
    "type" : "NON_EU",
    "iso2Code" : "MU",
    "nonEUMemberState" : True
    }, {
    "name" : "Mayotte",
    "type" : "NON_EU",
    "iso2Code" : "YT",
    "nonEUMemberState" : True
    }, {
    "name" : "Mexico",
    "type" : "NON_EU",
    "iso2Code" : "MX",
    "nonEUMemberState" : True
    }, {
    "name" : "Monaco",
    "type" : "NON_EU",
    "iso2Code" : "MC",
    "nonEUMemberState" : True
    }, {
    "name" : "Mongolia",
    "type" : "NON_EU",
    "iso2Code" : "MN",
    "nonEUMemberState" : True
    }, {
    "name" : "Montenegro",
    "type" : "NON_EU",
    "iso2Code" : "ME",
    "nonEUMemberState" : True
    }, {
    "name" : "Morocco",
    "type" : "NON_EU",
    "iso2Code" : "MA",
    "nonEUMemberState" : True
    }, {
    "name" : "Mozambique",
    "type" : "NON_EU",
    "iso2Code" : "MZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Myanmar",
    "type" : "NON_EU",
    "iso2Code" : "MM",
    "nonEUMemberState" : True
    }, {
    "name" : "Namibia",
    "type" : "NON_EU",
    "iso2Code" : "NA",
    "nonEUMemberState" : True
    }, {
    "name" : "Nauru",
    "type" : "NON_EU",
    "iso2Code" : "NR",
    "nonEUMemberState" : True
    }, {
    "name" : "Nepal",
    "type" : "NON_EU",
    "iso2Code" : "NP",
    "nonEUMemberState" : True
    }, {
    "name" : "Netherlands",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "NL",
    "nonEUMemberState" : False
    }, {
    "name" : "Netherlands Antilles",
    "type" : "NON_EU",
    "iso2Code" : "AN",
    "nonEUMemberState" : True
    }, {
    "name" : "New Caledonia",
    "type" : "NON_EU",
    "iso2Code" : "NC",
    "nonEUMemberState" : True
    }, {
    "name" : "New Zealand",
    "type" : "NON_EU",
    "iso2Code" : "NZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Nicaragua",
    "type" : "NON_EU",
    "iso2Code" : "NI",
    "nonEUMemberState" : True
    }, {
    "name" : "Niger",
    "type" : "NON_EU",
    "iso2Code" : "NE",
    "nonEUMemberState" : True
    }, {
    "name" : "Nigeria",
    "type" : "NON_EU",
    "iso2Code" : "NG",
    "nonEUMemberState" : True
    }, {
    "name" : "Niue",
    "type" : "NON_EU",
    "iso2Code" : "NU",
    "nonEUMemberState" : True
    }, {
    "name" : "Norfolk Island",
    "type" : "NON_EU",
    "iso2Code" : "NF",
    "nonEUMemberState" : True
    }, {
    "name" : "Northern Mariana Islands",
    "type" : "NON_EU",
    "iso2Code" : "MP",
    "nonEUMemberState" : True
    }, {
    "name" : "Norway",
    "type" : "EU_EXTENDED",
    "iso2Code" : "NO",
    "nonEUMemberState" : False
    }, {
    "name" : "Occupied Palestinian Territory",
    "type" : "NON_EU",
    "iso2Code" : "PS",
    "nonEUMemberState" : True
    }, {
    "name" : "Oman",
    "type" : "NON_EU",
    "iso2Code" : "OM",
    "nonEUMemberState" : True
    }, {
    "name" : "Pakistan",
    "type" : "NON_EU",
    "iso2Code" : "PK",
    "nonEUMemberState" : True
    }, {
    "name" : "Palau",
    "type" : "NON_EU",
    "iso2Code" : "PW",
    "nonEUMemberState" : True
    }, {
    "name" : "Panama",
    "type" : "NON_EU",
    "iso2Code" : "PA",
    "nonEUMemberState" : True
    }, {
    "name" : "Papua New Guinea",
    "type" : "NON_EU",
    "iso2Code" : "PG",
    "nonEUMemberState" : True
    }, {
    "name" : "Paraguay",
    "type" : "NON_EU",
    "iso2Code" : "PY",
    "nonEUMemberState" : True
    }, {
    "name" : "Peru",
    "type" : "NON_EU",
    "iso2Code" : "PE",
    "nonEUMemberState" : True
    }, {
    "name" : "Philippines",
    "type" : "NON_EU",
    "iso2Code" : "PH",
    "nonEUMemberState" : True
    }, {
    "name" : "Poland",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "PL",
    "nonEUMemberState" : False
    }, {
    "name" : "Portugal",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "PT",
    "nonEUMemberState" : False
    }, {
    "name" : "Puerto Rico",
    "type" : "NON_EU",
    "iso2Code" : "PR",
    "nonEUMemberState" : True
    }, {
    "name" : "Qatar",
    "type" : "NON_EU",
    "iso2Code" : "QA",
    "nonEUMemberState" : True
    }, {
    "name" : "Republic of Korea",
    "type" : "NON_EU",
    "iso2Code" : "KR",
    "nonEUMemberState" : True
    }, {
    "name" : "Republic of Moldova",
    "type" : "NON_EU",
    "iso2Code" : "MD",
    "nonEUMemberState" : True
    }, {
    "name" : "Republic of North Macedonia",
    "type" : "NON_EU",
    "iso2Code" : "MK",
    "nonEUMemberState" : True
    }, {
    "name" : "Republic of the Congo",
    "type" : "NON_EU",
    "iso2Code" : "CG",
    "nonEUMemberState" : True
    }, {
    "name" : "Romania",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "RO",
    "nonEUMemberState" : False
    }, {
    "name" : "Russian Federation",
    "type" : "NON_EU",
    "iso2Code" : "RU",
    "nonEUMemberState" : True
    }, {
    "name" : "Rwanda",
    "type" : "NON_EU",
    "iso2Code" : "RW",
    "nonEUMemberState" : True
    }, {
    "name" : "Réunion",
    "type" : "NON_EU",
    "iso2Code" : "RE",
    "nonEUMemberState" : True
    }, {
    "name" : "Saint Helena",
    "type" : "NON_EU",
    "iso2Code" : "SH",
    "nonEUMemberState" : True
    }, {
    "name" : "Saint Kitts and Nevis",
    "type" : "NON_EU",
    "iso2Code" : "KN",
    "nonEUMemberState" : True
    }, {
    "name" : "Saint Lucia",
    "type" : "NON_EU",
    "iso2Code" : "LC",
    "nonEUMemberState" : True
    }, {
    "name" : "Saint Vincent and the Grenadines",
    "type" : "NON_EU",
    "iso2Code" : "VC",
    "nonEUMemberState" : True
    }, {
    "name" : "Saint-Pierre and Miquelon",
    "type" : "NON_EU",
    "iso2Code" : "PM",
    "nonEUMemberState" : True
    }, {
    "name" : "Samoa",
    "type" : "NON_EU",
    "iso2Code" : "WS",
    "nonEUMemberState" : True
    }, {
    "name" : "San Marino",
    "type" : "NON_EU",
    "iso2Code" : "SM",
    "nonEUMemberState" : True
    }, {
    "name" : "Sao Tome and Principe",
    "type" : "NON_EU",
    "iso2Code" : "ST",
    "nonEUMemberState" : True
    }, {
    "name" : "Saudi Arabia",
    "type" : "NON_EU",
    "iso2Code" : "SA",
    "nonEUMemberState" : True
    }, {
    "name" : "Senegal",
    "type" : "NON_EU",
    "iso2Code" : "SN",
    "nonEUMemberState" : True
    }, {
    "name" : "Serbia",
    "type" : "NON_EU",
    "iso2Code" : "RS",
    "nonEUMemberState" : True
    }, {
    "name" : "Seychelles",
    "type" : "NON_EU",
    "iso2Code" : "SC",
    "nonEUMemberState" : True
    }, {
    "name" : "Sierra Leone",
    "type" : "NON_EU",
    "iso2Code" : "SL",
    "nonEUMemberState" : True
    }, {
    "name" : "Singapore",
    "type" : "NON_EU",
    "iso2Code" : "SG",
    "nonEUMemberState" : True
    }, {
    "name" : "Slovakia",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "SK",
    "nonEUMemberState" : False
    }, {
    "name" : "Slovenia",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "SI",
    "nonEUMemberState" : False
    }, {
    "name" : "Solomon Islands",
    "type" : "NON_EU",
    "iso2Code" : "SB",
    "nonEUMemberState" : True
    }, {
    "name" : "Somalia",
    "type" : "NON_EU",
    "iso2Code" : "SO",
    "nonEUMemberState" : True
    }, {
    "name" : "South Africa",
    "type" : "NON_EU",
    "iso2Code" : "ZA",
    "nonEUMemberState" : True
    }, {
    "name" : "South Sudan",
    "type" : "NON_EU",
    "iso2Code" : "SS",
    "nonEUMemberState" : True
    }, {
    "name" : "Spain",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "ES",
    "nonEUMemberState" : False
    }, {
    "name" : "Sri Lanka",
    "type" : "NON_EU",
    "iso2Code" : "LK",
    "nonEUMemberState" : True
    }, {
    "name" : "Sudan",
    "type" : "NON_EU",
    "iso2Code" : "SD",
    "nonEUMemberState" : True
    }, {
    "name" : "Suriname",
    "type" : "NON_EU",
    "iso2Code" : "SR",
    "nonEUMemberState" : True
    }, {
    "name" : "Svalbard and Jan Mayen",
    "type" : "NON_EU",
    "iso2Code" : "SJ",
    "nonEUMemberState" : True
    }, {
    "name" : "Sweden",
    "type" : "EU_MEMBER_STATE",
    "iso2Code" : "SE",
    "nonEUMemberState" : False
    }, {
    "name" : "Switzerland",
    "type" : "NON_EU",
    "iso2Code" : "CH",
    "nonEUMemberState" : True
    }, {
    "name" : "Syrian Arab Republic",
    "type" : "NON_EU",
    "iso2Code" : "SY",
    "nonEUMemberState" : True
    }, {
    "name" : "Taiwan",
    "type" : "NON_EU",
    "iso2Code" : "TW",
    "nonEUMemberState" : True
    }, {
    "name" : "Tajikistan",
    "type" : "NON_EU",
    "iso2Code" : "TJ",
    "nonEUMemberState" : True
    }, {
    "name" : "Thailand",
    "type" : "NON_EU",
    "iso2Code" : "TH",
    "nonEUMemberState" : True
    }, {
    "name" : "The Democratic Republic Of The Congo",
    "type" : "NON_EU",
    "iso2Code" : "CD",
    "nonEUMemberState" : True
    }, {
    "name" : "Timor-Leste",
    "type" : "NON_EU",
    "iso2Code" : "TL",
    "nonEUMemberState" : True
    }, {
    "name" : "Togo",
    "type" : "NON_EU",
    "iso2Code" : "TG",
    "nonEUMemberState" : True
    }, {
    "name" : "Tokelau",
    "type" : "NON_EU",
    "iso2Code" : "TK",
    "nonEUMemberState" : True
    }, {
    "name" : "Tonga",
    "type" : "NON_EU",
    "iso2Code" : "TO",
    "nonEUMemberState" : True
    }, {
    "name" : "Trinidad and Tobago",
    "type" : "NON_EU",
    "iso2Code" : "TT",
    "nonEUMemberState" : True
    }, {
    "name" : "Tunisia",
    "type" : "NON_EU",
    "iso2Code" : "TN",
    "nonEUMemberState" : True
    }, {
    "name" : "Turkmenistan",
    "type" : "NON_EU",
    "iso2Code" : "TM",
    "nonEUMemberState" : True
    }, {
    "name" : "Tuvalu",
    "type" : "NON_EU",
    "iso2Code" : "TV",
    "nonEUMemberState" : True
    }, {
    "name" : "Türkiye",
    "type" : "EU_EXTENDED",
    "iso2Code" : "TR",
    "nonEUMemberState" : False
    }, {
    "name" : "U.S. Virgin Islands",
    "type" : "NON_EU",
    "iso2Code" : "VI",
    "nonEUMemberState" : True
    }, {
    "name" : "Uganda",
    "type" : "NON_EU",
    "iso2Code" : "UG",
    "nonEUMemberState" : True
    }, {
    "name" : "Ukraine",
    "type" : "NON_EU",
    "iso2Code" : "UA",
    "nonEUMemberState" : True
    }, {
    "name" : "United Arab Emirates",
    "type" : "NON_EU",
    "iso2Code" : "AE",
    "nonEUMemberState" : True
    }, {
    "name" : "United Kingdom (Northern Ireland only)",
    "type" : "EU_SPECIAL",
    "iso2Code" : "XI",
    "nonEUMemberState" : False
    }, {
    "name" : "United Kingdom (excl. Northern Ireland)",
    "type" : "NON_EU",
    "iso2Code" : "UK",
    "nonEUMemberState" : True
    }, {
    "name" : "United Republic Of Tanzania",
    "type" : "NON_EU",
    "iso2Code" : "TZ",
    "nonEUMemberState" : True
    }, {
    "name" : "United States",
    "type" : "NON_EU",
    "iso2Code" : "US",
    "nonEUMemberState" : True
    }, {
    "name" : "United States Minor Outlying Islands",
    "type" : "NON_EU",
    "iso2Code" : "UM",
    "nonEUMemberState" : True
    }, {
    "name" : "Uruguay",
    "type" : "NON_EU",
    "iso2Code" : "UY",
    "nonEUMemberState" : True
    }, {
    "name" : "Uzbekistan",
    "type" : "NON_EU",
    "iso2Code" : "UZ",
    "nonEUMemberState" : True
    }, {
    "name" : "Vanuatu",
    "type" : "NON_EU",
    "iso2Code" : "VU",
    "nonEUMemberState" : True
    }, {
    "name" : "Vatican City State",
    "type" : "NON_EU",
    "iso2Code" : "VA",
    "nonEUMemberState" : True
    }, {
    "name" : "Venezuela",
    "type" : "NON_EU",
    "iso2Code" : "VE",
    "nonEUMemberState" : True
    }, {
    "name" : "Vietnam",
    "type" : "NON_EU",
    "iso2Code" : "VN",
    "nonEUMemberState" : True
    }, {
    "name" : "Wallis and Futuna",
    "type" : "NON_EU",
    "iso2Code" : "WF",
    "nonEUMemberState" : True
    }, {
    "name" : "Western Sahara",
    "type" : "NON_EU",
    "iso2Code" : "EH",
    "nonEUMemberState" : True
    }, {
    "name" : "Yemen",
    "type" : "NON_EU",
    "iso2Code" : "YE",
    "nonEUMemberState" : True
    }, {
    "name" : "Zambia",
    "type" : "NON_EU",
    "iso2Code" : "ZM",
    "nonEUMemberState" : True
    }, {
    "name" : "Zimbabwe",
    "type" : "NON_EU",
    "iso2Code" : "ZW",
    "nonEUMemberState" : True
    }, {
    "name" : "Åland Islands",
    "type" : "NON_EU",
    "iso2Code" : "AX",
    "nonEUMemberState" : True
    } 
]

# Insert countries into the table
for country in countries:
    restrctured_country = {
        'name': country['name'],
        'iso_code': country['iso2Code'],
        'non_EU_Member_State': country['nonEUMemberState'],
        'type': country['type']
    }

    supabase.table('countries').insert(restrctured_country).execute()

