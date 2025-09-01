# Crew Job Review System

## Overview

The Crew Job Review system enables comprehensive job opportunity evaluation through AI-powered analysis and human review. The system guides users through multiple steps to ensure job applications are properly analyzed and tailored to their strategic narrative.

## Job Review Workflow

### Step 1: Initial Input
- Users paste job description or job URL
- AI extracts initial details from the input
- Option to mark as "message-only" application

### Step 2: Job Details Review
The job details review step allows users to verify and edit AI-extracted information:

#### Current Fields (JobDetailsReviewStep)
- **Company Name**: Required field for the employing organization
- **Company Homepage URL**: Optional company website URL
- **Job Title**: Required field for the position title  
- **Salary**: Optional compensation information

#### Enhanced Fields (Should Match JobDetailsStep)
- **Job Description**: Full job posting with markdown preview capability
- **Location**: Job location information
- **Remote Status**: Remote/Hybrid/On-site classification
- **Strategic Narrative**: Selection of applicable narrative for tailoring

### Step 3: Company Confirmation
- Match or create company in system
- Research company details if needed

### Step 4: AI Problem Analysis
- AI analyzes job requirements against strategic narrative
- Generates strategic fit score
- Identifies key success metrics and assumptions

### Step 5: Resume/Message Tailoring
- Select base resume for tailoring
- AI generates keyword-optimized content
- Option for message-only applications

## Component Architecture

### JobDetailsReviewStep.tsx
**Current Implementation:**
- Basic form with 4 fields only
- Limited validation (company name and job title required)
- No job description editing capability
- Missing narrative selection

**Recommended Enhancements:**
- Add job description field with markdown preview
- Include location and remote status fields
- Add strategic narrative selection
- Implement comprehensive validation
- Match functionality of JobDetailsStep.tsx

### JobDetailsStep.tsx
**Current Implementation:**
- Comprehensive job details editing
- Markdown preview for job description
- Location and remote status fields
- Strategic narrative selection
- Tab-based editing interface

**Usage:**
This component is more comprehensive and should serve as the model for enhancing JobDetailsReviewStep.

## Data Flow

```
Initial Input → AI Extraction → Job Details Review → Company Confirmation → AI Analysis
```

### Key Data Structures

```typescript
type JobDetailsPayload = {
  companyName: string;
  isRecruitingFirm: boolean;
  jobTitle: string;
  jobLink: string;
  salary: string;
  location: string;
  remoteStatus: 'Remote' | 'Hybrid' | 'On-site' | '';
  jobDescription: string;
}
```

## AI Integration

The system integrates with Gemini AI for:
- Job detail extraction from pasted content
- Strategic fit analysis
- Keyword generation
- Resume tailoring recommendations

## Database Integration

Job data is persisted through the Python service with fields mapped to the database schema. See `python-service/JOBS_PERSISTENCE.md` for details on data persistence.

## User Experience Guidelines

1. **Progressive Disclosure**: Start with essential fields, expand as needed
2. **Visual Feedback**: Show loading states during AI processing
3. **Validation**: Provide clear error messages and field requirements
4. **Consistency**: Maintain consistent styling and behavior across review steps

## Known Issues & Improvements

1. **Inconsistent Components**: JobDetailsReviewStep is less comprehensive than JobDetailsStep
2. **Missing Fields**: Location, remote status, and job description not in review step
3. **No Preview**: Review step lacks markdown preview capability
4. **Navigation**: Need consistent step navigation and validation

## Implementation Priority

1. **High**: Enhance JobDetailsReviewStep to match JobDetailsStep functionality
2. **Medium**: Add comprehensive validation and error handling
3. **Low**: Implement advanced preview and editing features