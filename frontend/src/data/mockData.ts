import { Resume, ReviewedJob, PaginatedResponse } from '../types';

export const BLANK_RESUME_CONTENT: Resume = {
  header: {
      first_name: "",
      last_name: "",
      job_title: "",
      email: "",
      phone_number: "",
      city: "",
      state: "",
      links: []
  },
  summary: {
    paragraph: "",
    bullets:[]
  },
  work_experience: [],
  education: [],
  certifications: [],
  skills: []
};

// Mock data for demonstrating HITL Review Flow
export const MOCK_REVIEWED_JOBS: PaginatedResponse<ReviewedJob> = {
  items: [
    {
      job_id: "550e8400-e29b-41d4-a716-446655440001",
      url: "https://example.com/job1",
      title: "Senior Software Engineer",
      company_name: "TechCorp",
      location: "San Francisco, CA",
      date_posted: "2024-01-15T00:00:00Z",
      recommendation: "Recommended",
      confidence: 0.9,
      overall_alignment_score: 8.5,
      is_eligible_for_application: true,
      rationale: "This role aligns well with your background in full-stack development and your experience with React and Node.js. The company culture emphasizes innovation and work-life balance, which matches your career preferences.",
      confidence_level: "high",
      // No override data - AI recommendation stands
    },
    {
      job_id: "550e8400-e29b-41d4-a716-446655440002",
      url: "https://example.com/job2",
      title: "Product Manager",
      company_name: "StartupCo",
      location: "Remote",
      date_posted: "2024-01-14T00:00:00Z",
      recommendation: "Not Recommended",
      confidence: 0.6,
      overall_alignment_score: 4.2,
      is_eligible_for_application: false,
      rationale: "While the role offers growth opportunities, it requires extensive product management experience that doesn't align with your technical background. The startup environment may also involve longer hours.",
      confidence_level: "medium",
      // This job has been overridden by human reviewer
      override_recommend: true,
      override_comment: "Despite the AI's concerns, this role offers excellent learning opportunities and the team culture is a perfect fit. The candidate's technical background will actually be an asset in a technical product management role.",
      override_by: "hiring_manager",
      override_at: "2024-01-15T10:30:00Z",
    },
    {
      job_id: "550e8400-e29b-41d4-a716-446655440003",
      url: "https://example.com/job3", 
      title: "DevOps Engineer",
      company_name: "CloudTech",
      location: "Austin, TX",
      date_posted: "2024-01-13T00:00:00Z",
      recommendation: "Recommended",
      confidence: 0.7,
      overall_alignment_score: 7.1,
      is_eligible_for_application: true,
      rationale: "Good match for your infrastructure automation skills. The role involves working with modern cloud technologies and CI/CD pipelines that align with your experience.",
      confidence_level: "medium",
    }
  ],
  total: 3,
  page: 1,
  size: 15,
  pages: 1
};