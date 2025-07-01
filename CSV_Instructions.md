# Country Data CSV Template - Instructions

## Overview
This CSV template captures all the information needed to add a new country to the visa website's MongoDB database. Please fill out all **required** fields and as many optional fields as possible to provide comprehensive visa information.

## General Guidelines

### Required vs Optional Fields
- **Required fields** marked as "Yes" in the Required column MUST be filled
- **Optional fields** marked as "No" can be left empty if information is not available
- **Boolean fields** should only contain `true` or `false` (lowercase)

### Data Formatting

#### Text Fields
- Use plain text without special formatting
- For long descriptions, keep them concise but informative
- Avoid using commas in text fields to prevent CSV parsing issues

#### Multiple Values (Pipe Separated)
When a field asks for multiple values separated by pipes (|), format like this:
```
Value 1|Value 2|Value 3
```
Example: `Tourist Visa|Business Visa|Transit Visa`

#### Boolean Fields
- Use `true` for yes/enabled
- Use `false` for no/disabled
- Always lowercase

#### Number Fields
- Use numbers without currency symbols
- Use decimal points for fractional amounts (e.g., 1234.50)

## Field Categories Explained

### Basic Information
These are the core country details that appear on the website:
- **name**: Official country name as commonly known
- **flag**: Country flag emoji (copy from official sources)
- **slug**: URL-friendly identifier (lowercase, hyphens instead of spaces)
- **region**: Choose from: Asia, Europe, Africa, Americas, Oceania

### Visa Types
You can define up to 3 different visa types. Common types include:
- Tourist/Visit Visa
- Business Visa
- Transit Visa
- Student Visa
- Work Visa

### Documents
List up to 8 different required documents. For each document specify:
- **category options**: mandatory, for_minors, for_business, conditional
- **format options**: original, photocopy, scan

### Photo Requirements
Specify passport photo requirements:
- **size**: Exact dimensions (e.g., "35mm x 45mm", "2x2 inches")
- **background**: Usually "white" or "light blue"
- **specifications**: Use pipe separator for multiple specs

### Processing Times
Up to 3 different processing options:
- **type**: regular, express, priority, emergency
- **duration**: Specific timeframe (e.g., "3-5 working days")

### Fees
Up to 2 fee types (usually visa fee + service fee):
- Include amounts in INR, USD, and local currency when available
- **local_currency**: Use 3-letter currency codes (USD, EUR, SGD, etc.)

### Application Methods
Up to 3 application methods:
- **name options**: embassy, online, voa (visa on arrival), agent
- Use pipe separator for multiple requirements

### Embassies
Up to 2 embassy/consulate locations:
- Include complete contact information
- Provide official website URLs

### Special Information
- **Entry Points**: List major airports, land borders, seaports
- **Transit Info**: Visa-free transit details if available
- **Special Conditions**: Any unique requirements
- **Important Notes**: Critical information for travelers

## Example Entry
Here's how a typical entry might look:

```csv
Basic_Info,name,text,Yes,Official country name,Singapore,
Basic_Info,flag,text,Yes,Country flag emoji,🇸🇬,
Basic_Info,slug,text,Yes,URL-friendly identifier,singapore,
Basic_Info,region,text,Yes,Geographical region,Asia,
Basic_Info,visa_required,boolean,Yes,Whether visa is required,true,
```

## Common Mistakes to Avoid

1. **Don't use commas in text fields** - This breaks CSV parsing
2. **Don't leave required fields empty** - These will cause validation errors
3. **Don't use mixed case for boolean values** - Use only `true` or `false`
4. **Don't forget pipe separators** - Use | to separate multiple values
5. **Don't use currency symbols in number fields** - Use plain numbers only

## After Completion

1. Save the file as a CSV format
2. Double-check all required fields are filled
3. Verify contact information is accurate
4. Ensure fee amounts are current
5. Submit the completed CSV for review and import

## Support

If you have questions about any specific fields or need clarification on requirements, please contact the development team for assistance. 