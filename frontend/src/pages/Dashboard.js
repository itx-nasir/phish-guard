import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../utils/constants';
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Tab,
  Tabs,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Dashboard = () => {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [emailContent, setEmailContent] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationErrors, setValidationErrors] = useState({});
  const [selectedFiles, setSelectedFiles] = useState([]);

  // Validation functions
  const validateEmailContent = useCallback((content) => {
    const errors = {};
    
    if (!content || !content.trim()) {
      errors.content = 'Email content is required';
    } else if (content.length < 50) {
      errors.content = 'Email content seems too short (minimum 50 characters)';
    } else if (content.length > 1024 * 1024) {
      errors.content = 'Email content is too large (maximum 1MB)';
    }
    
    // Basic email format validation
    if (content && !content.includes('@') && !content.toLowerCase().includes('from:')) {
      errors.format = 'This doesn\'t appear to be valid email content';
    }
    
    return errors;
  }, []);

  const validateFiles = useCallback((files) => {
    const errors = [];
    
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith('.eml')) {
        errors.push(`${file.name}: Only .eml files are supported`);
      }
      
      if (file.size > 16 * 1024 * 1024) {
        errors.push(`${file.name}: File size must be less than 16MB`);
      }
      
      if (file.size === 0) {
        errors.push(`${file.name}: File appears to be empty`);
      }
    }
    
    return errors;
  }, []);

  // Error handling
  const handleError = useCallback((err, context = 'operation') => {
    console.error(`Error in ${context}:`, err);
    
    let errorMessage = 'An unexpected error occurred';
    
    if (err.response?.data?.details) {
      errorMessage = err.response.data.details;
    } else if (err.response?.data?.error) {
      errorMessage = err.response.data.error;
    } else if (err.message) {
      errorMessage = err.message;
    }
    
    setError(errorMessage);
  }, []);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError(null);
    setValidationErrors({});
    setSelectedFiles([]);
  };

  const handleBatchUpload = async (files) => {
    setError(null);
    setIsLoading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files[]', file);
      });

      const response = await axios.post(API_ENDPOINTS.ANALYZE_BATCH, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });
      
      if (response.data.task_ids) {
        // Navigate to batch results page
        navigate('/batch-analysis', { 
          state: { taskIds: response.data.task_ids }
        });
      } else {
        throw new Error('No task IDs received from server');
      }
    } catch (err) {
      handleError(err, 'batch upload');
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
    }
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: {
      'message/rfc822': ['.eml'],
    },
    maxSize: 16 * 1024 * 1024, // 16MB
    multiple: true, // Enable multiple file selection
    onDrop: async (acceptedFiles, rejectedFiles) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const errors = rejectedFiles.map(rejection => {
          if (rejection.errors.some(e => e.code === 'file-too-large')) {
            return `${rejection.file.name}: File is too large. Maximum size is 16MB.`;
          } else if (rejection.errors.some(e => e.code === 'file-invalid-type')) {
            return `${rejection.file.name}: Invalid file type. Please select an .eml file.`;
          }
          return `${rejection.file.name}: File validation failed.`;
        });
        setError(errors.join('\n'));
        return;
      }

      if (acceptedFiles.length > 0) {
        if (acceptedFiles.length > 10) {
          setError('Maximum 10 files can be uploaded at once');
          return;
        }

        const fileErrors = validateFiles(acceptedFiles);
        if (fileErrors.length > 0) {
          setError(fileErrors.join('\n'));
          return;
        }

        setSelectedFiles(acceptedFiles);
        await handleBatchUpload(acceptedFiles);
      }
    }
  });

  const handleContentSubmit = async () => {
    // Validate content
    const contentErrors = validateEmailContent(emailContent);
    setValidationErrors(contentErrors);
    
    if (Object.keys(contentErrors).length > 0) {
      setError('Please fix the validation errors before submitting');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const response = await axios.post('/api/analyze/content', {
        content: emailContent,
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000, // 30 second timeout
      });
      
      if (response.data.task_id) {
        navigate(`/analysis/${response.data.task_id}`);
      } else {
        throw new Error('No task ID received from server');
      }
    } catch (err) {
      handleError(err, 'content analysis');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailContentChange = (e) => {
    const value = e.target.value;
    setEmailContent(value);
    
    // Clear validation errors as user types
    if (validationErrors.content && value.trim().length >= 50) {
      setValidationErrors(prev => ({ ...prev, content: null }));
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Email Phishing Analysis
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload one or multiple email files (.eml) or paste email content to analyze for potential phishing threats.
        Our advanced detection system will examine headers, content, links, and attachments.
      </Typography>

      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="analysis method tabs">
              <Tab label="Upload Files" id="tab-0" aria-controls="tabpanel-0" />
              <Tab label="Paste Content" id="tab-1" aria-controls="tabpanel-1" />
            </Tabs>
          </Box>

          {/* Loading progress bar */}
          {isLoading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress 
                variant={uploadProgress > 0 ? "determinate" : "indeterminate"} 
                value={uploadProgress}
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {uploadProgress > 0 
                  ? `Uploading... ${uploadProgress}%` 
                  : 'Processing your request...'
                }
              </Typography>
            </Box>
          )}

          {/* Error display */}
          {error && (
            <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{error}</pre>
            </Alert>
          )}

          <TabPanel value={tabValue} index={0}>
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragReject 
                  ? 'error.main' 
                  : isDragActive 
                    ? 'primary.main' 
                    : 'grey.300',
                borderRadius: 1,
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive ? 'primary.50' : 'inherit',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'primary.50',
                },
                ...(isLoading && {
                  pointerEvents: 'none',
                  opacity: 0.6,
                }),
              }}
            >
              <input {...getInputProps()} />
              {isLoading ? (
                <Box>
                  <CircularProgress size={24} sx={{ mb: 2 }} />
                  <Typography>Processing files...</Typography>
                </Box>
              ) : (
                <>
                  <Typography>
                    {isDragReject
                      ? 'Some files are not supported'
                      : isDragActive
                        ? 'Drop the files here'
                        : 'Drag and drop .eml files here, or click to select files'
                    }
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Maximum 10 files • Maximum size per file: 16MB • Supported format: .eml
                  </Typography>
                  {selectedFiles.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Selected Files:
                      </Typography>
                      <List dense>
                        {selectedFiles.map((file, index) => (
                          <ListItem key={index}>
                            <ListItemText
                              primary={file.name}
                              secondary={`${(file.size / 1024).toFixed(1)} KB`}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                </>
              )}
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  multiline
                  rows={10}
                  fullWidth
                  placeholder="Paste email content here..."
                  value={emailContent}
                  onChange={handleEmailContentChange}
                  error={!!(validationErrors.content || validationErrors.format)}
                  helperText={validationErrors.content || validationErrors.format || `${emailContent.length}/1,048,576 characters`}
                  disabled={isLoading}
                  inputProps={{
                    'aria-label': 'Email content',
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Button
                    variant="contained"
                    onClick={handleContentSubmit}
                    disabled={isLoading || !emailContent.trim() || Object.keys(validationErrors).length > 0}
                    startIcon={isLoading ? <CircularProgress size={20} /> : null}
                  >
                    {isLoading ? 'Analyzing...' : 'Analyze Content'}
                  </Button>
                  
                  {emailContent.trim() && (
                    <Typography variant="body2" color="text.secondary">
                      Ready to analyze {Math.round(emailContent.length / 1024)}KB of content
                    </Typography>
                  )}
                </Box>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard; 