import React, { useState } from 'react';
import axios from 'axios';
import { BookOpen, Send, Clock, Upload, FileText } from 'lucide-react';

const CreateExam = ({ user }) => {
  const [examData, setExamData] = useState({
    title: '',
    subject: '',
    startTime: '',
    endTime: '',
    strength: '',
  });

  const [isDeploying, setIsDeploying] = useState(false);

  // Question Paper (PDF/Image)
  const [questionPaper, setQuestionPaper] = useState({
    fileName: '',
    base64: ''
  });

  // Optional Answer Key
  const [answerKey, setAnswerKey] = useState({
    fileName: '',
    base64: ''
  });

  // Convert file → Base64 (JSON-safe)
  const handleFileUpload = (e, setter) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      setter({
        fileName: file.name,
        base64: reader.result
      });
    };
    reader.readAsDataURL(file);
  };

  const handleDeploy = async (e) => {
    e.preventDefault();
    setIsDeploying(true);

    const payload = {
      ...examData,
      teacherId: user.id,
      questionPaper: questionPaper, // REQUIRED
      answerKey: answerKey           // OPTIONAL
    };

    try {
      await axios.post(
        'http://10.88.42.48:5000/api/create-exam-full',
        payload
      );
      alert("Exam Portal Deployed Successfully!");
    } catch (err) {
      console.error("Deployment failed:", err);
      alert("Error deploying exam portal.");
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Deployment Console</h1>
        <p className="text-slate-500 font-medium">
          Upload question paper and configure exam timeline
        </p>
      </div>

      <form onSubmit={handleDeploy} className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* LEFT PANEL */}
        <div className="space-y-6 bg-white p-6 rounded-3xl border shadow-sm">

          <h3 className="font-bold text-slate-800 flex items-center gap-2">
            <BookOpen size={18} className="text-blue-600" /> Exam Information
          </h3>

          <input
            required
            type="text"
            placeholder="Exam Title"
            className="w-full p-3 bg-slate-50 rounded-xl"
            onChange={(e) =>
              setExamData({ ...examData, title: e.target.value })
            }
          />

          <input
            required
            type="text"
            placeholder="Subject Code"
            className="w-full p-3 bg-slate-50 rounded-xl"
            onChange={(e) =>
              setExamData({ ...examData, subject: e.target.value })
            }
          />

          <div className="grid grid-cols-2 gap-4">
            <input
              required
              type="datetime-local"
              className="p-3 bg-slate-50 rounded-xl"
              onChange={(e) =>
                setExamData({ ...examData, startTime: e.target.value })
              }
            />
            <input
              required
              type="datetime-local"
              className="p-3 bg-slate-50 rounded-xl"
              onChange={(e) =>
                setExamData({ ...examData, endTime: e.target.value })
              }
            />
          </div>

          {/* QUESTION PAPER UPLOAD */}
          <div>
            <label className="text-xs font-bold text-slate-500">
              Upload Question Paper (PDF / Image)
            </label>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              className="hidden"
              id="questionPaper"
              required
              onChange={(e) => handleFileUpload(e, setQuestionPaper)}
            />
            <label
              htmlFor="questionPaper"
              className="flex items-center gap-2 p-4 mt-2 border-2 border-dashed rounded-xl cursor-pointer"
            >
              <Upload size={16} />
              {questionPaper.fileName || "Select Question Paper"}
            </label>
          </div>

          {/* ANSWER KEY (OPTIONAL) */}
          <div>
            <label className="text-xs font-bold text-slate-500">
              Upload Answer Key (Optional)
            </label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              className="hidden"
              id="answerKey"
              onChange={(e) => handleFileUpload(e, setAnswerKey)}
            />
            <label
              htmlFor="answerKey"
              className="flex items-center gap-2 p-4 mt-2 border-2 border-dashed rounded-xl cursor-pointer"
            >
              <FileText size={16} />
              {answerKey.fileName || "Select Answer Key"}
            </label>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="flex items-end justify-end">
          <button
            disabled={isDeploying}
            className="flex items-center gap-3 bg-slate-900 text-white px-10 py-4 rounded-2xl font-bold hover:bg-blue-600 disabled:bg-slate-300"
          >
            {isDeploying ? "Deploying..." : <><Send size={18} /> Deploy Exam</>}
          </button>
        </div>

      </form>
    </div>
  );
};

export default CreateExam;
