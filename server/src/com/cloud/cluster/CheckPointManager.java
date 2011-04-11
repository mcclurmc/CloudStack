package com.cloud.cluster;


/**
 * TaskManager helps business logic deal with clustering failover.
 * Say you're writing code that introduces an inconsistent state over
 * a long period of time.  What happens if the server died in the middle 
 * of your operation?  Who will come back to cleanup this state?  TaskManager
 * will help with doing this.  You can create a task and update the state
 * with different content during your process.  If the server dies, TaskManager
 * will automatically cleanup the tasks if there is a clustered server 
 * running elsewhere.  If there are no clustered servers, then TaskManager will
 * cleanup when the dead server resumes.
 *
 */
public interface CheckPointManager {
    /**
     * Adds a task with the context as to what the task is and the class
     * responsible for cleaning up.
     * 
     * @param context context information to be stored.
     * @return Check point id.
     */
    long pushCheckPoint(CleanupMaid context);
    
    /**
     * update the task with new context
     * @param taskId
     * @param updatedContext new updated context.
     */
    void updateCheckPointState(long taskId, CleanupMaid updatedContext);
    
    
    /**
     * removes the task as it is completed.
     * 
     * @param taskId
     */
    void popCheckPoint(long taskId);
}