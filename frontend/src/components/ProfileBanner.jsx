import React from "react";

const ProfileBanner = ({ user, profile }) => {
  const displayName =
    user?.display_name || `${user?.first_name || ""} ${user?.last_name || ""}`.trim() || user?.email || "Student";

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-center md:items-start justify-between gap-6">
      <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
        <div className="relative">
          <div className="w-24 h-24 bg-indigo-100 rounded-2xl overflow-hidden border-4 border-white shadow-md">
            <img src={user?.avatar_url || "https://i.pravatar.cc/300?img=11"} alt="User Avatar" className="w-full h-full object-cover" />
          </div>
        </div>

        <div className="text-center md:text-left">
          <h1 className="text-2xl font-bold text-slate-800">{displayName}</h1>
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mt-2">
            <span className="bg-indigo-50 text-indigo-700 text-xs font-bold px-3 py-1 rounded-full">
              {profile?.sss_level || "SSS"} • Term {profile?.current_term || "-"}
            </span>
            <span className="bg-amber-50 text-amber-700 text-xs font-bold px-3 py-1 rounded-full">
              {(profile?.subjects || []).join(", ") || "No subjects"}
            </span>
          </div>
          <p className="text-slate-500 text-sm mt-3">✉ {user?.email || "-"}</p>
        </div>
      </div>
    </div>
  );
};

export default ProfileBanner;
