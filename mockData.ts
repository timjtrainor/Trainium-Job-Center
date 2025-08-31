import { Resume } from './types';

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