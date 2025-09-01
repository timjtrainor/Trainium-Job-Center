import React from 'react';
import { JobDetailsReviewStep } from '../components/JobDetailsReviewStep';

// Mock data for testing
const mockJobDetails = {
  companyName: 'TechCorp Inc.',
  isRecruitingFirm: false,
  jobTitle: 'Senior Software Engineer',
  jobLink: 'https://techcorp.com/careers/senior-engineer',
  salary: '$120,000 - $150,000',
  location: 'San Francisco, CA',
  remoteStatus: 'Hybrid' as const,
  jobDescription: '## About the Role\n\nWe are looking for a passionate Senior Software Engineer to join our team.\n\n### Requirements\n- 5+ years of experience\n- React and TypeScript expertise\n- Strong problem-solving skills'
};

const mockNarratives = [
  {
    narrative_id: '1',
    narrative_name: 'Full-Stack Leadership',
    positioning_statement: 'Senior engineer with team leadership experience',
    signature_capability: 'React/Node.js development',
    desired_title: 'Senior Software Engineer',
    compensation_expectation: '$140,000',
    default_resume_id: null,
    impact_story_body: 'Led team of 5 engineers...'
  },
  {
    narrative_id: '2', 
    narrative_name: 'AI/ML Specialist',
    positioning_statement: 'Machine learning engineer with production experience',
    signature_capability: 'Python/ML model deployment',
    desired_title: 'Machine Learning Engineer',
    compensation_expectation: '$160,000',
    default_resume_id: null,
    impact_story_body: 'Deployed ML models...'
  }
];

// Test component to demonstrate the enhanced JobDetailsReviewStep
export const TestJobDetailsReviewStep = () => {
  const handleNext = (payload: any) => {
    console.log('Job details submitted:', payload);
    alert('Job details review completed successfully!');
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>Enhanced Job Details Review Step - Test</h1>
      <JobDetailsReviewStep
        onNext={handleNext}
        isLoading={false}
        initialJobDetails={mockJobDetails}
        narratives={mockNarratives}
        selectedNarrativeId="1"
      />
    </div>
  );
};