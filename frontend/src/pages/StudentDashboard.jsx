// src/pages/StudentDashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Book, GraduationCap, LogOut, Calendar, FileText } from 'lucide-react';
import Results from './Results'; 

const StudentDashboard = ({ user, onLogout }) => {
  const [exams, setExams] = useState(null); // null = loading
  const [activeTab, setActiveTab] = useState('exams');
  const [selectedExamId, setSelectedExamId] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);

  // -------- FETCH ACTIVE EXAMS --------
  useEffect(() => {
    axios.get(`http://localhost:5000/api/exams?studentId=${user.id}`)
      .then(res => {
        setExams(res.data || []);
      })
      .catch(err => {
        console.error(err);
        setExams([]);
      });
  }, [user.id]);

  // -------- HANDLE SUBMISSION --------
  const handleUpload = async (e) => {
    e.preventDefault();

    if (!uploadFile) {
      alert("Please select a file before submitting.");
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('studentId', user.id);
    formData.append('examId', selectedExamId);

    try {
      await axios.post('http://localhost:5000/api/upload-script', formData);
      alert("Answer Script Uploaded Successfully!");

      // 🔥 refresh exams
      const res = await axios.get(
        `http://localhost:5000/api/exams?studentId=${user.id}`
      );
      setExams(res.data);
      setSelectedExamId(null);
      setUploadFile(null);
    } catch (err) {
      alert(err.response?.data?.message || "Submission failed.");
    }
  };

  return (
    <div className="flex min-h-screen bg-[#F8FAFC]">

      {/* -------- SIDEBAR -------- */}
      <aside className="w-72 bg-[#1A1C4B] text-white flex flex-col fixed h-full shadow-2xl">
        <div className="p-8">
          <div className="flex items-center gap-3 mb-10">
            <div className="bg-white p-2 rounded-lg">
              <GraduationCap className="text-[#1A1C4B]" size={24} />
            </div>
            <div>
              <h1 className="text-xl font-black">EDU-GRADE</h1>
              <p className="text-[10px] text-blue-300 font-bold uppercase">AI Governance</p>
            </div>
          </div>

          <div className="bg-white/10 p-4 rounded-2xl mb-8">
            <p className="text-[10px] text-blue-200 font-bold uppercase mb-2">Authenticated As</p>
            <p className="font-bold text-sm truncate">{user.name}</p>
            <span className="mt-2 inline-block bg-blue-500 text-[10px] font-black px-2 py-0.5 rounded uppercase">
              {user.role}
            </span>
          </div>

          <nav className="space-y-3">
            <button
              onClick={() => setActiveTab('exams')}
              className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl font-bold text-sm ${activeTab === 'exams' ? 'bg-blue-600' : 'text-slate-400 hover:bg-white/5'}`}
            >
              <Book size={18} /> Exams
            </button>

            <button
              onClick={() => setActiveTab('performance')}
              className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl font-bold text-sm ${activeTab === 'performance' ? 'bg-blue-600' : 'text-slate-400 hover:bg-white/5'}`}
            >
              <GraduationCap size={18} /> My Performance
            </button>
          </nav>
        </div>

        <div className="mt-auto p-8 border-t border-white/5">
          <button onClick={onLogout} className="flex items-center gap-3 text-slate-400 hover:text-white font-bold text-sm">
            <LogOut size={18} /> Log Out
          </button>
        </div>
      </aside>

      {/* -------- MAIN CONTENT -------- */}
      <main className="flex-1 ml-72 p-12">
        <header className="mb-10">
          <h2 className="text-3xl font-black text-[#1A1C4B]">
            {activeTab === 'exams' ? 'Academic Portal' : 'Results Pipeline'}
          </h2>
          <p className="text-slate-500 font-medium">
            REAL-TIME EXAMINATION LIFECYCLE MANAGEMENT
          </p>
        </header>

        <div className="bg-white rounded-[40px] border p-10 min-h-[500px]">
          {activeTab === 'exams' ? (
            exams === null ? (
              <p className="text-center text-slate-400 font-bold">Loading exams...</p>
            ) : exams.length > 0 ? (
              exams.map(exam => (
                <ExamCard key={exam.id} exam={exam} onUpload={() => setSelectedExamId(exam.id)} />
              ))
            ) : (
              <EmptyState message="NO EXAMINATIONS SCHEDULED" />
            )
          ) : (
            <Results user={user} />
          )}
        </div>
      </main>

      {/* -------- UPLOAD MODAL -------- */}
      {selectedExamId && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white p-10 rounded-[32px] w-full max-w-md">
            <h3 className="text-xl font-black mb-4">Upload Answer Script</h3>
            <form onSubmit={handleUpload} className="space-y-6">
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => setUploadFile(e.target.files[0])}
              />
              <div className="flex gap-4">
                <button className="flex-1 bg-blue-600 text-white py-3 rounded-xl font-black">
                  SUBMIT
                </button>
                <button type="button" onClick={() => setSelectedExamId(null)} className="flex-1 bg-slate-100 py-3 rounded-xl">
                  CANCEL
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

// -------- HELPERS --------

const ExamCard = ({ exam, onUpload }) => {
  // const isExpired = new Date() > new Date(exam.end_time);
  const now = new Date().getTime();
  const end = new Date(exam.end_time).getTime();
  const isExpired = now > end;


  return (
    // <div className="flex justify-between p-6 bg-slate-50 rounded-3xl mb-6">
    //   <div>
    //     <h4 className="font-bold text-lg">{exam.title}</h4>
    //     <p className="text-xs uppercase text-slate-400">{exam.subject}</p>
    //   </div>
    //   {!isExpired ? (
    //     <button onClick={onUpload} className="bg-[#1A1C4B] text-white px-6 py-3 rounded-xl font-black text-xs">
    //       UPLOAD SCRIPT
    //     </button>
    //   ) : (
    //     <span className="text-xs bg-slate-200 px-4 py-2 rounded-full">Closed</span>
    //   )}
    // </div>
    
    <div className="flex justify-between p-6 bg-slate-50 rounded-3xl mb-6">
      <div>
        <h4 className="font-bold text-lg">{exam.title}</h4>
        <p className="text-xs uppercase text-slate-400">{exam.subject}</p>
        <span
          className={`text-[10px] font-bold uppercase mt-1 inline-block ${
            exam.status === "active"
              ? "text-green-600"
              : exam.status === "upcoming"
              ? "text-blue-600"
              : "text-red-500"
          }`}
        >
          {exam.status}
        </span>
      </div>

      {/* {exam.status === "active" ? (
        <button
          onClick={onUpload}
          className="bg-[#1A1C4B] text-white px-6 py-3 rounded-xl font-black text-xs"
        >
          UPLOAD SCRIPT
        </button>
      ) : exam.status === "upcoming" ? (
        <span className="text-xs bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-bold">
          Not started yet
        </span>
      ) : (
        <span className="text-xs bg-slate-200 px-4 py-2 rounded-full">
          Closed
        </span>
      )} */}
      {exam.submitted ? (
  <span className="text-xs bg-green-100 text-green-700 px-4 py-2 rounded-full font-bold">
    Submitted
  </span>
) : exam.status === "active" ? (
  <button
    onClick={onUpload}
    className="bg-[#1A1C4B] text-white px-6 py-3 rounded-xl font-black text-xs"
  >
    UPLOAD SCRIPT
  </button>
) : exam.status === "upcoming" ? (
  <span className="text-xs bg-blue-100 text-blue-700 px-4 py-2 rounded-full font-bold">
    Not started yet
  </span>
) : (
  <span className="text-xs bg-slate-200 px-4 py-2 rounded-full">
    Closed
  </span>
)}

    </div>
  );
};

const EmptyState = ({ message }) => (
  <div className="flex flex-col items-center justify-center py-20 opacity-40">
    <Calendar size={64} />
    <p className="mt-6 font-black tracking-widest">{message}</p>
  </div>
);

export default StudentDashboard;
