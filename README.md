# Job Data to Internship Schema Transformer

This Python script transforms job search data from SerpAPI or local JSON files into a clean internship schema format.

## Features

- ✅ **Dual Input Support**: Works with both local JSON files and live SerpAPI URLs
- ✅ **Smart Location Extraction**: Automatically extracts location from job titles (e.g., "Job in Mumbai" → "Job" + location: "Mumbai")
- ✅ **Clean Data Format**: Outputs structured internship data without schema repetition
- ✅ **Comprehensive Data Extraction**: Extracts job title, location, salary, description, and time period
- ✅ **Error Handling**: Graceful handling of missing data and API errors

## Usage

### Option 1: Using Local JSON File (Default)
```bash
python transform_data.py
# or
python transform_data.py data.json
# or
python transform_data.py data.json output.json
```

### Option 2: Using SerpAPI URL
```bash
python transform_data.py "https://serpapi.com/search.json?engine=google_jobs&q=python+backend+fullstack+internship+parttime&location=India&api_key=YOUR_API_KEY"
```

### Option 3: Using SerpAPI URL with Custom Output File
```bash
python transform_data.py "https://serpapi.com/search.json?engine=google_jobs&q=data+scientist+internship&location=USA&api_key=YOUR_API_KEY" "data_science_internships.json"
```

## SerpAPI URL Format

The script accepts SerpAPI URLs with the following format:
```
https://serpapi.com/search.json?engine=google_jobs&q=SEARCH_QUERY&location=LOCATION&api_key=YOUR_API_KEY
```

### Parameters:
- `engine=google_jobs` (required)
- `q=SEARCH_QUERY` (required) - Your job search query
- `location=LOCATION` (optional) - Location to search in
- `api_key=YOUR_API_KEY` (required for SerpAPI)

### Example Queries:
- `q=python+backend+fullstack+internship+parttime`
- `q=data+scientist+internship+remote`
- `q=frontend+developer+intern+react`
- `q=machine+learning+internship`

## Output Format

The script generates a clean JSON format:

```json
{
  "internships": [
    {
      "job_title": "Full Stack Developer Intern",
      "description": "About the job: Full Stack Developer Internship...",
      "location": "Mumbai, India",
      "salary": "₹240K–₹360K a year",
      "time_period": "Full-time, Posted 2 days ago, Duration: 3 months"
    }
  ],
  "total_count": 10,
  "source": "Transformed from SerpAPI job search results",
  "schema_version": "1.0"
}
```

## Schema Fields

Each internship entry contains:
- **job_title** (required): Clean job title with location extracted
- **description** (required): Job description (truncated to 500 chars)
- **location** (optional): Location extracted from title or original location
- **salary** (optional): Salary information when available
- **time_period** (optional): Schedule type, posting date, and duration

## Requirements

- Python 3.6+
- requests library (`pip install requests`)

## Examples

### Search for Python Internships in India
```bash
python transform_data.py "https://serpapi.com/search.json?engine=google_jobs&q=python+internship&location=India&api_key=YOUR_API_KEY"
```

### Search for Remote Data Science Internships
```bash
python transform_data.py "https://serpapi.com/search.json?engine=google_jobs&q=data+science+internship+remote&api_key=YOUR_API_KEY"
```

### Search for Frontend Internships in USA
```bash
python transform_data.py "https://serpapi.com/search.json?engine=google_jobs&q=frontend+internship+react&location=USA&api_key=YOUR_API_KEY"
```

## Getting SerpAPI Key

1. Sign up at [SerpAPI](https://serpapi.com/)
2. Get your free API key from the dashboard
3. Replace `YOUR_API_KEY` in the URL with your actual API key

## Error Handling

The script handles various error scenarios:
- Invalid SerpAPI URLs
- Network connectivity issues
- Missing or malformed JSON data
- API rate limits and errors
- File not found errors

## Notes

- The script automatically detects whether the input is a URL or file path
- Location extraction works for patterns like "Job Title in Location"
- Descriptions are truncated to 500 characters for readability
- The script preserves all original data while cleaning and structuring it
