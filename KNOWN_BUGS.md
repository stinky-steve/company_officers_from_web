# Known Bugs and Issues

## DataReader Class
1. `DataReader` initialization requires both MinIO client and bucket name, but some code paths still try to initialize with only bucket name
2. File cleanup in working directories sometimes fails due to file locks
3. JSON processing errors occur when files are corrupted or in unexpected format

## File Handling
1. Working directory cleanup fails with error: `[WinError 32] The process cannot access the file because it is being used by another process`
2. Directory removal fails with error: `[WinError 145] The directory is not empty`
3. Some files remain locked after processing, preventing cleanup

## MinIO Integration
1. MinIO client initialization needs to be properly handled in all code paths
2. File download errors occur when MinIO client is not properly initialized
3. Some file operations fail with `'NoneType' object has no attribute 'fget_object'`

## Data Processing
1. JSON parsing errors occur with malformed files
2. Some company data is missing required fields (website, company_name)
3. Domain extraction fails for some URLs
4. People deduplication may not catch all cases

## Database Operations
1. Database operations are not properly handling all error cases
2. Some management officers may be duplicated in the database
3. Missing proper validation before database insertions

## General Issues
1. Error handling needs improvement throughout the codebase
2. Logging could be more detailed and structured
3. Some functions lack proper type hints
4. Code organization could be improved for better maintainability

## Next Steps
1. Implement proper file locking mechanism
2. Add better error handling for JSON processing
3. Improve MinIO client initialization and error handling
4. Add data validation before database operations
5. Implement better logging system
6. Add proper type hints throughout the codebase
7. Improve code organization and documentation 