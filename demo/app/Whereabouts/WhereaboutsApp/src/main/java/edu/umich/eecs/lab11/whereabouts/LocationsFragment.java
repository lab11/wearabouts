/*
 * Copyright (C) 2013 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package edu.umich.eecs.lab11.whereabouts;

import android.app.Activity;
import android.app.Fragment;
import android.content.Context;
import android.os.Bundle;
import android.os.Handler;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.BaseExpandableListAdapter;
import android.widget.ExpandableListView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.google.gson.JsonObject;

import java.util.ArrayList;

/**
 * Activity for scanning and displaying available Bluetooth LE devices.
 */
public class LocationsFragment extends Fragment {

    private JsonObject profiles;
    private Activity fa;
    private ExpandListAdapter ExpAdapter;
    private ArrayList<ExpandListGroup> ExpListItems;
    private ExpandableListView ExpandList;
    private WebView myWebView;
    final Handler myHandler = new Handler();

    static LocationsFragment newInstance(int num) {
        LocationsFragment f = new LocationsFragment();
        Bundle args = new Bundle();
        args.putInt("num", num);
        f.setArguments(args);

        return f;
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        fa = super.getActivity();
        View v = inflater.inflate(R.layout.fragment_web, container, false);
        final JavaScriptInterface myJavaScriptInterface = new JavaScriptInterface(fa);
        myWebView = (WebView) v.findViewById(R.id.webview);
        WebSettings webSettings = myWebView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);
//        myWebView.loadUrl("file:///android_asset/index.html");
//        myWebView.addJavascriptInterface(myJavaScriptInterface, "AndroidFunction");
//        myWebView.loadUrl("javascript:socket.emit('query', {'profile_id':'hsYQx8blbd','time': 120*60*1000 } );");
//        ExpListItems = new ArrayList<ExpandListGroup>();
//        ExpandList = (ExpandableListView) v.findViewById(R.id.ExpList);
//        ExpAdapter = new ExpandListAdapter(fa, ExpListItems);
//        ExpandList.setAdapter(ExpAdapter);
//        ExpandList.setEmptyView(v.findViewById(android.R.id.empty));
//        myWebView.loadUrl("http://gatd.eecs.umich.edu/whereabouts.html");
        myWebView.loadUrl("file:///android_asset/index.html");
//        myWebView.loadUrl("javascript:socket.emit('query', {'profile_id':'hsYQx8blbd','time': 120*60*1000 } );");
        return (LinearLayout) v;
    }

    public class JavaScriptInterface {
        Context mContext;

        JavaScriptInterface(Context c) {
            mContext = c;
        }

        @JavascriptInterface
        public void showToast(String webMessage){
            final String message = webMessage;
            String[] args = message.split("::");
            if (args[0].equals("WHEREABOUTS")) {
                ExpandListGroup a = new ExpandListGroup(args[1]);
                int pos = ExpAdapter.addGroup(a);
                for (int i = 2; i < args.length; i++) ExpAdapter.addItem(args[i], a);
                ExpAdapter.notifyDataSetChanged();
                ExpandList.expandGroup(pos);
            }
        }
    }

    private class ExpandListChild {
        private String Name;
        public ExpandListChild(String Name) { this.Name=Name; }
        public String getName() { return Name; }
        public void setName(String Name) { this.Name = Name; }
    }

    private class ExpandListGroup {
        private String Name;
        private ArrayList<ExpandListChild> Items;
        public ExpandListGroup(String Name) { this.Name = Name; this.Items=new ArrayList<ExpandListChild>(); }
        public String getName() { return Name; }
        public void setName(String Name) { this.Name = Name; }
        public ArrayList<ExpandListChild> getItems() { return Items; }
        public void setItems(ArrayList<ExpandListChild> Items) { this.Items = Items; }
        @Override public boolean equals(Object o) { return (o instanceof ExpandListGroup) && Name.equals(((ExpandListGroup) o).getName()); }
    }

    private class ExpandListAdapter extends BaseExpandableListAdapter {

        private Context context;
        private ArrayList<ExpandListGroup> groups;
        public ExpandListAdapter(Context context, ArrayList<ExpandListGroup> groups) {
            this.context = context;
            this.groups = groups;
        }
        public int addGroup(ExpandListGroup group) {
            if (groups.contains(group)) groups.remove(group);
            groups.add(group);
            return groups.indexOf(group);
        }
        public void addItem(String item, ExpandListGroup group) {
            int index = groups.indexOf(group);
            ArrayList<ExpandListChild> ch = groups.get(index).getItems();
            ch.add(new ExpandListChild(item));
            groups.get(index).setItems(ch);
        }
        public Object getChild(int groupPosition, int childPosition) {
            ArrayList<ExpandListChild> chList = groups.get(groupPosition).getItems();
            return chList.get(childPosition);
        }

        public long getChildId(int groupPosition, int childPosition) {
            return childPosition;
        }

        public View getChildView(int groupPosition, int childPosition, boolean isLastChild, View view,
                                 ViewGroup parent) {
            ExpandListChild child = (ExpandListChild) getChild(groupPosition, childPosition);
            if (view == null) {
                LayoutInflater infalInflater = (LayoutInflater) context.getSystemService(context.LAYOUT_INFLATER_SERVICE);
                view = infalInflater.inflate(R.layout.listitem_device, null);
            }
            TextView tv = (TextView) view.findViewById(R.id.device_name);
            tv.setText(child.getName().toString());
            return view;
        }

        public int getChildrenCount(int groupPosition) {
            ArrayList<ExpandListChild> chList = groups.get(groupPosition).getItems();
            return chList.size();
        }

        public Object getGroup(int groupPosition) {
            return groups.get(groupPosition);
        }

        public int getGroupCount() {
            return groups.size();
        }

        public long getGroupId(int groupPosition) {
            return groupPosition;
        }

        public View getGroupView(int groupPosition, boolean isExpanded, View view,
                                 ViewGroup parent) {
            ExpandListGroup group = (ExpandListGroup) getGroup(groupPosition);
            if (view == null) {
                LayoutInflater inf = (LayoutInflater) context.getSystemService(context.LAYOUT_INFLATER_SERVICE);
                view = inf.inflate(R.layout.sectionitem_device, null);
            }
            TextView tv = (TextView) view.findViewById(R.id.tvGroup);
            tv.setText(group.getName());
            return view;
        }

        public boolean hasStableIds() {
            return true;
        }

        public boolean isChildSelectable(int arg0, int arg1) {
            return false;
        }

    }

}