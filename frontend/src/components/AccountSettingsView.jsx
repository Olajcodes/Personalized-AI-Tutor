import React, { useEffect, useState } from "react";

const AccountSettingsView = ({ user, profile, onSave, saving }) => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    display_name: "",
    phone: "",
    avatar_url: "",
  });

  useEffect(() => {
    setFormData({
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      display_name: user?.display_name || "",
      phone: user?.phone || "",
      avatar_url: user?.avatar_url || "",
    });
  }, [user]);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const submit = (e) => {
    e.preventDefault();
    onSave?.(formData);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-800">Account Information</h2>
        <p className="text-sm text-slate-500 mb-6">Update your personal details.</p>

        <form className="space-y-5" onSubmit={submit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">First Name</label>
              <input type="text" name="first_name" value={formData.first_name} onChange={handleChange} className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Last Name</label>
              <input type="text" name="last_name" value={formData.last_name} onChange={handleChange} className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Display Name</label>
              <input type="text" name="display_name" value={formData.display_name} onChange={handleChange} className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Phone</label>
              <input type="text" name="phone" value={formData.phone} onChange={handleChange} className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow" />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-slate-700">Avatar URL</label>
            <input type="url" name="avatar_url" value={formData.avatar_url} onChange={handleChange} className="w-full border border-slate-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow" />
          </div>

          <div className="pt-4 flex justify-end">
            <button type="submit" disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold py-2.5 px-6 rounded-lg transition-colors">
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-5">Learning Scope</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-4 p-4 border border-slate-100 bg-slate-50 rounded-xl">
            <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-lg">🎓</div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">SSS Level</p>
              <p className="font-bold text-slate-800">{profile?.sss_level || "-"}</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 border border-slate-100 bg-slate-50 rounded-xl">
            <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-lg">📅</div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Current Term</p>
              <p className="font-bold text-slate-800">{profile?.current_term || "-"}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccountSettingsView;
