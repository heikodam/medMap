# PARD-EUDAMED Company Name Matcher

This script compares company names between the `pard_company` and `eudamed_company` tables in Supabase and identifies matches.

## Features

- Fetches company data from both Supabase tables with pagination support (handles 10,000+ records)
- Normalizes company names for better matching (removing suffixes, case-insensitive, etc.)
- Generates a CSV file with all PARD company names and whether they match an EUDAMED company
- Provides a summary of match statistics

## Scripts

There are two versions of the matcher:

1. **Basic Matcher** (`pard_eudamed_matcher.py`): Uses exact matching after normalization
2. **Fuzzy Matcher** (`pard_eudamed_matcher_fuzzy.py`): Uses fuzzy string matching for better results

## Requirements

- Python 3.6+
- Required packages: see project's main `requirements.txt`
- Supabase credentials in `.env` file

## Usage

1. Make sure your `.env` file contains the Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

2. Run one of the scripts:
   ```
   # For basic matching
   python -m pard_eudamed_match.pard_eudamed_matcher
   
   # For fuzzy matching (recommended)
   python -m pard_eudamed_match.pard_eudamed_matcher_fuzzy
   ```

3. Check the output CSV file:
   ```
   # Basic matching results
   pard_eudamed_match/pard_eudamed_matches.csv
   
   # Fuzzy matching results
   pard_eudamed_match/pard_eudamed_matches_fuzzy.csv
   ```

## Output

### Basic Matcher Output
The CSV file contains two columns:
- `pard_name`: The company name from the PARD database
- `match_found`: Boolean indicating whether a match was found in the EUDAMED database (TRUE/FALSE)

### Fuzzy Matcher Output
The CSV file contains the following columns:
- `pard_name`: The company name from the PARD database
- `exact_match`: Boolean indicating an exact match after normalization (TRUE/FALSE)
- `fuzzy_match`: Boolean indicating whether a fuzzy match was found (TRUE/FALSE)
- `match_score`: The similarity score (0-100) of the best match found
- `best_match`: The normalized name of the best match found in EUDAMED

## Customization

- If you need to modify the matching algorithm, you can edit the `normalize_company_name` function to include additional normalization steps.
- For the fuzzy matcher, you can adjust the `threshold` parameter in the `compare_companies_fuzzy` function call (default is 85). Lower values will include more potential matches but may introduce false positives. 