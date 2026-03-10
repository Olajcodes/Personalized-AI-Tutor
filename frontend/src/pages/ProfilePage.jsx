import React, { useState } from 'react';
import ProfileBanner from '../components/ProfileBanner';
import SettingsSidebar from '../components/SettingsSidebar';
import AccountSettingsView from '../components/AccountSettingsView';
import LearningPreferencesView from '../components/LearningPreferencesView';
import { profileData } from '../mocks/profileData';
import { useUser } from '../context/UserContext';
import { useAuth } from '../context/AuthContext'; // <-- Added to get the token
import { updateUserProfile } from '../services/api'; // <-- Added to hit your backend

const ProfilePage = () => {
  const [activeTab, setActiveTab] = useState('account');
  const [isUploading, setIsUploading] = useState(false); // Track upload status
  
  const { token } = useAuth();
  const { userData, studentData, updateLocalUser } = useUser();

  // --- Cloudinary Config ---
  const CLOUDINARY_CLOUD_NAME = "dzt3imk5w"; 
  const CLOUDINARY_UPLOAD_PRESET = "masteryai_avatars"; 

  // ======================================================================
  // 1. IMAGE UPLOAD LOGIC (Moved to the Parent Layout!)
  // ======================================================================
  const handleImageUpload = async (file) => {
    setIsUploading(true);

    try {
      // Step A: Send file to Cloudinary
      const uploadData = new FormData();
      uploadData.append('file', file);
      uploadData.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);

      const cloudinaryRes = await fetch(
        `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`,
        { method: 'POST', body: uploadData }
      );

      if (!cloudinaryRes.ok) throw new Error("Cloudinary upload failed");

      const cloudinaryData = await cloudinaryRes.json();
      const imageUrl = cloudinaryData.secure_url; 

      // Step B: Save to backend
      await updateUserProfile(token, { avatar_url: imageUrl });

      // Step C: Update global state so the UI refreshes instantly
      updateLocalUser({ avatar_url: imageUrl });
      
    } catch (error) {
      console.error("Upload Error:", error);
      alert("Failed to update profile picture. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  // ======================================================================
  // 2. DATA BLENDING
  // ======================================================================
 const activeUser = {
    ...profileData.user,
    // Add first and last name directly to the object so ProfileBanner can use them!
    first_name: userData?.first_name,
    last_name: userData?.last_name,
    name: userData ? `${userData.first_name || ''} ${userData.last_name || ''}`.trim() : profileData.user.name,
    email: userData?.email || profileData.user.email,
    gradeLevel: studentData?.sss_level || "SSS 1",
    league: "Gold League", 
    masteryPoints: studentData?.mastery_score || 0,
    
    // 👇 THE FIX: Set this to null so ProfileBanner's getInitials takes over
    avatarUrl: userData?.avatar_url || null
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-12">
      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        
        {/* --- Top Banner Area (ONLY ONE RENDERS ON THE PAGE!) --- */}
        <ProfileBanner 
          user={activeUser} 
          onImageUpload={handleImageUpload} // Pass the function down!
        />

        {/* Show a loading pulse if they just selected a new photo */}
        {isUploading && (
          <div className="p-4 bg-indigo-50 border border-indigo-200 text-indigo-700 rounded-2xl text-sm font-bold text-center animate-pulse shadow-sm">
            Uploading and saving your new avatar...
          </div>
        )}

        {/* --- Bottom Split Layout --- */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          
          <div className="md:col-span-3">
            <SettingsSidebar activeTab={activeTab} setActiveTab={setActiveTab} />
          </div>

          <div className="md:col-span-9">
            {activeTab === 'account' && (
              <AccountSettingsView 
                user={activeUser} 
                school={profileData.school} 
                security={profileData.security} 
              />
            )}
            {activeTab === 'preferences' && <LearningPreferencesView />}
            {activeTab === 'mastery' && <div className="p-8 bg-white rounded-xl shadow-sm border border-slate-200">Mastery coming soon...</div>}
          </div>

        </div>
      </main>
    </div>
  );
};

export default ProfilePage;