import React, { useState } from 'react';
import { complaintsAPI } from '../api/complaints';
import './FeedbackForm.css';

interface FeedbackFormProps {
  complaintId: string;
  onSuccess?: () => void;
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({ complaintId, onSuccess }) => {
  const [rating, setRating] = useState(0);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (rating === 0) {
      setError('Please select a rating');
      return;
    }

    setLoading(true);

    try {
      await complaintsAPI.submitFeedback(complaintId, {
        rating,
        comments,
      });

      setSuccess(true);
      
      if (onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to submit feedback');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="feedback-success">
        <div className="success-icon">✓</div>
        <h3>Thank you for your feedback!</h3>
        <p>Your input helps us improve our service</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="feedback-form">
      <div className="form-group">
        <label>How satisfied are you with the resolution?</label>
        <div className="star-rating">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              className={`star ${star <= (hoveredRating || rating) ? 'active' : ''}`}
              onClick={() => setRating(star)}
              onMouseEnter={() => setHoveredRating(star)}
              onMouseLeave={() => setHoveredRating(0)}
              disabled={loading}
            >
              ★
            </button>
          ))}
        </div>
        <div className="rating-labels">
          <span>Poor</span>
          <span>Excellent</span>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="comments">Additional Comments (Optional)</label>
        <textarea
          id="comments"
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          placeholder="Share your experience or suggestions..."
          rows={4}
          disabled={loading}
        />
      </div>

      {error && <div className="error">{error}</div>}

      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Feedback'}
      </button>
    </form>
  );
};

export default FeedbackForm;
