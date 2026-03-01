import React, { useEffect, useState } from "react";
import ProfileBanner from "../components/ProfileBanner";
import SettingsSidebar from "../components/SettingsSidebar";
import AccountSettingsView from "../components/AccountSettingsView";
import LearningPreferencesView from "../components/LearningPreferencesView";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

const ProfilePage = () => {
  const { token, userId, user, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState("account");
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    (async () => {
      if (!token || !userId) return;
      setLoading(true);
      setError("");
      try {
        const [me, studentProfile] = await Promise.all([api.getUserMe(token), api.getProfile(token)]);
        if (!active) return;
        refreshUser(me);
        setProfile(studentProfile);
        setPreferences(studentProfile.preferences || null);
      } catch (err) {
        if (!active) return;
        setError(err.message || "Failed to load profile.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [token, userId, refreshUser]);

  const handleSaveAccount = async (payload) => {
    if (!token) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api.updateUserMe(token, payload);
      refreshUser(updated);
    } catch (err) {
      setError(err.message || "Failed to update account.");
    } finally {
      setSaving(false);
    }
  };

  const handleSavePreferences = async (payload) => {
    if (!token || !userId) return;
    setSaving(true);
    setError("");
    try {
      const updated = await api.updatePreferences(token, userId, payload);
      setPreferences(updated);
    } catch (err) {
      setError(err.message || "Failed to update preferences.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-slate-700">Loading profile...</div>;

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {error && <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">{error}</div>}
        <ProfileBanner user={user} profile={profile} />

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          <div className="md:col-span-3">
            <SettingsSidebar activeTab={activeTab} setActiveTab={setActiveTab} />
          </div>
          <div className="md:col-span-9">
            {activeTab === "account" && (
              <AccountSettingsView user={user} profile={profile} onSave={handleSaveAccount} saving={saving} />
            )}
            {activeTab === "preferences" && (
              <LearningPreferencesView preferences={preferences} onSave={handleSavePreferences} saving={saving} />
            )}
            {activeTab === "mastery" && <div className="p-8 bg-white rounded-xl shadow-sm border border-slate-200">Mastery insights are available on the Dashboard.</div>}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProfilePage;
