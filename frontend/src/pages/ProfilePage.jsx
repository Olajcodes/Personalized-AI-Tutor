import React, { useState } from 'react';
import ProfileBanner from '../components/ProfileBanner';
import SettingsSidebar from '../components/SettingsSidebar';
import AccountSettingsView from '../components/AccountSettingsView';
import LearningPreferencesView from '../components/LearningPreferencesView';
import { useUser } from '../context/UserContext';
import { useAuth } from '../context/AuthContext';
import { updateUserProfile } from '../services/api';

const ProfilePage = () => {
  const [activeTab, setActiveTab] = useState('account');
  const [isUploading, setIsUploading] = useState(false);

  const { token } = useAuth();
  const { userData, studentData, updateLocalUser } = useUser();

  const CLOUDINARY_CLOUD_NAME = 'dzt3imk5w';
  const CLOUDINARY_UPLOAD_PRESET = 'masteryai_avatars';

  const handleImageUpload = async (file) => {
    setIsUploading(true);

    try {
      const uploadData = new FormData();
      uploadData.append('file', file);
      uploadData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);

      const cloudinaryRes = await fetch(
        `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`,
        { method: 'POST', body: uploadData },
      );

      if (!cloudinaryRes.ok) throw new Error('Cloudinary upload failed');

      const cloudinaryData = await cloudinaryRes.json();
      const imageUrl = cloudinaryData.secure_url;
      await updateUserProfile(token, { avatar_url: imageUrl });
      updateLocalUser({ avatar_url: imageUrl });
    } catch (error) {
      console.error('Upload Error:', error);
      alert('Failed to update profile picture. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const activeUser = {
    first_name: userData?.first_name,
    last_name: userData?.last_name,
    name: `${userData?.first_name || ''} ${userData?.last_name || ''}`.trim() || 'Student',
    email: userData?.email || 'No email available',
    gradeLevel: studentData?.sss_level || 'Not set',
    league: studentData?.league_name || 'Learner',
    masteryPoints: Number(studentData?.mastery_score || 0),
    avatarUrl: userData?.avatar_url || null,
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <ProfileBanner user={activeUser} onImageUpload={handleImageUpload} />

        {isUploading && (
          <div className="p-4 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-2xl text-sm font-bold text-center animate-pulse shadow-sm">
            Uploading and saving your new avatar...
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          <div className="md:col-span-3">
            <SettingsSidebar activeTab={activeTab} setActiveTab={setActiveTab} />
          </div>

          <div className="md:col-span-9">
            {activeTab === 'account' && <AccountSettingsView user={activeUser} />}
            {activeTab === 'preferences' && <LearningPreferencesView />}
            {activeTab === 'mastery' && (
              <div className="p-8 bg-white rounded-xl shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-800">Mastery Overview</h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  Detailed mastery analytics are not available on this page yet. Use the dashboard, lesson graph,
                  and quiz results to inspect current concept strength and intervention history.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProfilePage;
